# User Context Notes

## The Traditional Data Modeling Workflow (The Full Picture)

The data architect/data modeller would sit down with business/SMEs, and together come up with a conceptual model, typically on a whiteboard, with some boxes and lines.

They would then build a conceptual model, followed by logical model in some top-heavy ER tool (like Erwin, PowerDesigner, etc.). From the logical model, they'd derive the physical model, and go to the engineers and say "we're building this."

The business would then come back and say "we need more", and together they extend the conceptual model on the whiteboard again. The architect would then go back to their ivory tower, update the conceptual model in the ER tool, refresh the logical model, derive an updated physical model, and again go to the engineers and say "we're changing this, and adding that."

Repeat ad infinitum.

### Key Points:

1. **Collaboration happened at the whiteboard** - not in the tool
2. **The tool work was solitary** - architect alone in their "ivory tower"
3. **Conceptual → Logical → Physical cascade** - rigid three-layer derivation
4. **Handoff culture** - "we're building this", "we're changing this"
5. **Cycle was asynchronous** - business asks → architect works alone → delivers to engineers
6. **The whiteboard was real, the ER tool was ceremony**

### What Actually Died:

- The assumption that one person (the architect) maintains the model
- The tooling that required specialized knowledge (expensive ER tools)
- The linear sequence: conceptual → logical → physical
- The handoff culture between roles
- The ivory tower isolation

### What This Means for dbt-conceptual:

The tool should:
- ✅ Enable the whiteboard experience (visual canvas)
- ✅ But make it collaborative, not solitary
- ✅ Live in git with the code, not in a proprietary tool
- ✅ Skip the logical model entirely (conceptual → dbt models directly)
- ✅ Be used by the engineers themselves, not handed to them

The positioning should emphasize:
- We kept what worked (conceptual thinking, visual collaboration)
- We ditched what didn't (ivory towers, specialized tools, three-layer cascade, handoffs)

---

*Recorded: 2026-01-19*
