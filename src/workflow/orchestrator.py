#!/usr/bin/env python3
"""
LangGraph Workflow Orchestration for learn_flow
Phase 2D: Orchestrates Agent 1 (Job Parser) → Agent 2 (Topic Assessor) → Database
"""
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from src.agents.job_parser import parse_jobs
from src.agents.topic_assessor import assess_topics, calculate_global_readiness
from src.core import database


class WorkflowState(TypedDict):
    """State passed between workflow nodes"""
    user_id: int
    form_data: dict
    path_id: str
    topics: list
    assessed_topics: list
    global_readiness: float
    error: str


def create_path_node(state: WorkflowState) -> WorkflowState:
    """
    Initial node: Create path in database
    """
    try:
        form_data = state["form_data"]
        path_id = database.create_path(
            user_id=state["user_id"],
            current_job_title=form_data["current_job_title"],
            current_description=form_data["current_description"],
            current_seniority=form_data["current_seniority"],
            target_job_title=form_data["target_job_title"],
            target_description=form_data["target_description"],
            target_seniority=form_data["target_seniority"],
            target_company=form_data.get("target_company", ""),
            target_industry=form_data.get("target_industry", ""),
            topics=[]
        )
        state["path_id"] = path_id
        print(f"  Path created: {path_id}")
    except Exception as e:
        state["error"] = f"Path creation failed: {e}"
        print(f"  ❌ Path creation error: {e}")

    return state


def agent1_parse_jobs(state: WorkflowState) -> WorkflowState:
    """
    Agent 1: Job Parser
    Extracts skill gaps from form data and generates topics
    """
    try:
        if state.get("error"):
            return state

        topics = parse_jobs(state["user_id"], state["form_data"])
        state["topics"] = topics
        print(f"  Agent 1 (Job Parser): {len(topics)} topics generated")
    except Exception as e:
        state["error"] = f"Agent 1 failed: {e}"
        print(f"  ❌ Agent 1 error: {e}")

    return state


def agent2_assess_topics(state: WorkflowState) -> WorkflowState:
    """
    Agent 2: Topic Assessor
    Breaks down topics into subtopics with mastery estimation
    """
    try:
        if state.get("error"):
            return state

        # Build current job context for mastery estimation
        form_data = state["form_data"]
        current_context = f"{form_data['current_seniority']} {form_data['current_job_title']}: {form_data['current_description']}"

        assessed_topics = assess_topics(
            state["user_id"],
            state["topics"],
            current_context
        )

        global_readiness = calculate_global_readiness(assessed_topics)

        state["assessed_topics"] = assessed_topics
        state["global_readiness"] = global_readiness

        print(f"  Agent 2 (Topic Assessor): {len(assessed_topics)} topics assessed")
        print(f"  Global readiness: {global_readiness}%")

    except Exception as e:
        state["error"] = f"Agent 2 failed: {e}"
        print(f"  ❌ Agent 2 error: {e}")

    return state


def save_to_database(state: WorkflowState) -> WorkflowState:
    """
    Final node: Save assessed topics to database
    Updates paths table and user_skills table
    """
    try:
        if state.get("error"):
            return state

        user_id = state["user_id"]
        path_id = state["path_id"]
        assessed_topics = state["assessed_topics"]
        global_readiness = state["global_readiness"]

        # Update paths table with global_readiness
        database.update_path_readiness(path_id, global_readiness, assessed_topics)

        # Insert/update user_skills for each topic
        for topic in assessed_topics:
            database.upsert_user_skill(
                user_id=user_id,
                topic_id=topic["topic_id"],
                mastery_percent=topic["mastery"],
                modules_complete=topic["modules_complete"],
                estimated_hours=topic["estimated_hours"]
            )

        print(f"  Database: {len(assessed_topics)} topics saved to paths + user_skills")

    except Exception as e:
        state["error"] = f"Database save failed: {e}"
        print(f"  ❌ Database error: {e}")

    return state


def build_workflow() -> StateGraph:
    """
    Build LangGraph workflow: CreatePath → Agent1 → Agent2 → Database

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("create_path", create_path_node)
    workflow.add_node("agent1_parse_jobs", agent1_parse_jobs)
    workflow.add_node("agent2_assess_topics", agent2_assess_topics)
    workflow.add_node("save_to_database", save_to_database)

    # Define edges (linear flow)
    workflow.set_entry_point("create_path")
    workflow.add_edge("create_path", "agent1_parse_jobs")
    workflow.add_edge("agent1_parse_jobs", "agent2_assess_topics")
    workflow.add_edge("agent2_assess_topics", "save_to_database")
    workflow.add_edge("save_to_database", END)

    return workflow.compile()


def run_full_workflow(user_id: int, form_data: dict) -> dict:
    """
    Execute full learning path generation workflow

    Args:
        user_id: User ID
        form_data: Screen 1 form data (12 fields from Phase 1)

    Returns:
        {
            "user_id": int,
            "path_id": str,
            "topics_count": int,
            "global_readiness": float,
            "assessed_topics": list,
            "error": str | None
        }
    """
    print(f"\n{'='*70}")
    print(f"Running workflow for User {user_id}")
    print(f"Path: {form_data['current_seniority']} {form_data['current_job_title']} → "
          f"{form_data['target_seniority']} {form_data['target_job_title']}")
    print(f"{'='*70}")

    # Initialize state
    initial_state = {
        "user_id": user_id,
        "form_data": form_data,
        "path_id": "",
        "topics": [],
        "assessed_topics": [],
        "global_readiness": 0.0,
        "error": None
    }

    # Build and run workflow
    workflow = build_workflow()
    final_state = workflow.invoke(initial_state)

    # Return results
    if final_state.get("error"):
        print(f"\n❌ Workflow failed: {final_state['error']}")
        return {
            "user_id": user_id,
            "path_id": "",
            "topics_count": 0,
            "global_readiness": 0.0,
            "assessed_topics": [],
            "error": final_state["error"]
        }

    print(f"\n✅ Workflow complete")
    print(f"   Path ID: {final_state['path_id']}")
    print(f"   {len(final_state['assessed_topics'])} topics → {final_state['global_readiness']}% readiness")

    return {
        "user_id": user_id,
        "path_id": final_state["path_id"],
        "topics_count": len(final_state["assessed_topics"]),
        "global_readiness": final_state["global_readiness"],
        "assessed_topics": final_state["assessed_topics"],
        "error": None
    }


if __name__ == "__main__":
    print("LangGraph Workflow ready.")
    print("Use: run_full_workflow(user_id, form_data)")
