// A tool the guard extension does not know, for the pi tests: it would write $PROBE_TOOL_FILE when run.
import { writeFileSync } from "node:fs";

export default function (pi: any) {
  pi.registerTool({
    name: "probe_tool",
    label: "Probe tool",
    description: "Writes a marker file.",
    parameters: { type: "object", properties: {}, additionalProperties: false },
    execute: async () => {
      writeFileSync(process.env.PROBE_TOOL_FILE || "/dev/null", "ran\n");
      return { content: [{ type: "text", text: "ran" }], details: {} };
    },
  });
}
