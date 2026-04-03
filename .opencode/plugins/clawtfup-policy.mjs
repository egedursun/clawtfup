/**
 * OpenCode / Kilocode plugin: run strict `clawtfup evaluate` after each tool execution.
 *
 * @see https://opencode.ai/docs/plugins
 * @see https://kilocode.ai/docs/cli
 */

import { spawnSync } from "node:child_process"
import { existsSync } from "node:fs"
import { join } from "node:path"
import { platform } from "node:os"

function clawtfupExecutable(root) {
  if (platform() === "win32") {
    const p = join(root, ".venv", "Scripts", "clawtfup.exe")
    if (existsSync(p)) {
      return p
    }
  } else {
    const p = join(root, ".venv", "bin", "clawtfup")
    if (existsSync(p)) {
      return p
    }
  }
  return "clawtfup"
}

function policiesDirPresent(root) {
  return existsSync(join(root, ".clawtfup", "policies"))
}

export const ClawtfupPolicy = async ({ directory }) => {
  if (!policiesDirPresent(directory)) {
    return {}
  }
  const exe = clawtfupExecutable(directory)
  return {
    "tool.execute.after": async (input) => {
      const tool = input && typeof input.tool === "string" ? input.tool : "tool"
      const result = spawnSync(exe, ["evaluate"], {
        cwd: directory,
        encoding: "utf-8",
        maxBuffer: 12 * 1024 * 1024,
      })
      if (result.error) {
        throw new Error(
          `clawtfup: could not run (${result.error.message}). Install clawtfup or fix PATH.`,
        )
      }
      const code = result.status
      if (code === 0) {
        return
      }
      const combined = [result.stdout, result.stderr].filter(Boolean).join("\n").trim()
      const clip =
        combined.length > 10000
          ? `${combined.slice(0, 10000)}\n...(truncated; run clawtfup evaluate --pretty locally.)`
          : combined
      throw new Error(`clawtfup: policy failed after ${tool}. Fix findings then retry.\n\n${clip}`)
    },
  }
}
