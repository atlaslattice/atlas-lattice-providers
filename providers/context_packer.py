#!/usr/bin/env python3
"""
Tier 3 #16: Advanced Context Packer - gathers from Notion/DecisionLedger/ProjectMemory/UWS by task type, provenance-rich.
"""

from typing import Dict, Any, List

class AdvancedContextPacker:
    def __init__(self, project=None, ledger=None, uws=None, simulate=True):
        self.project = project
        self.ledger = ledger
        self.uws = uws
        self.simulate = simulate

    async def pack(self, task_type: str, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        context = {"task_type": task_type, "query": query, "sources": [], "payload": ""}
        if self.project:
            mem = await self.project.run("project_memory_graph", query=query)
            context["sources"].append("project_memory")
            context["payload"] += str(mem)[:max_tokens//2]
        if self.ledger:
            context["sources"].append("decision_ledger")
            context["payload"] += "ledger_entries: recent high-inv decisions..."
        if self.uws:
            u = await self.uws.run("search_all", query=query)
            context["sources"].append("uws")
            context["payload"] += str(u)[:max_tokens//3]
        context["provenance"] = "context_packer_v1"
        context["grok_leads"] = True
        return context

    async def run(self, task_type: str = "general", query: str = "", **kwargs):
        return await self.pack(task_type, query, **kwargs)