# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.

# dsaas-batch
- **dsaas-batch** (`.claude/skills/dsaas-batch/SKILL.md`) - DSaaS component ideation loop: surveys 5 design systems, applies consensus rules, writes batch master prompt for the Figma agent. Trigger: `/dsaas-batch`
When the user types `/dsaas-batch [component list]`, invoke the Skill tool with `skill: "dsaas-batch"` before doing anything else.
