/**
 * Live Skill Authoring page — IDE-lite with Monaco editor + chat test panel.
 * Left panel (40%): file tree + editor
 * Right panel (60%): chat test + deploy controls
 */

"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FileTree } from "@/components/FileTree";
import { ChatTestPanel } from "@/components/ChatTestPanel";
import {
  listFiles,
  readFile,
  saveFile,
  deployApp,
  listVersions,
  rollback,
  type FileEntry,
  type SaveResult,
  type VersionEntry,
} from "@/lib/authoring-api";

// Dynamic import Monaco to avoid SSR issues
const Editor = dynamic(() => import("@monaco-editor/react").then((m) => m.default), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
      Loading editor...
    </div>
  ),
});

function getLanguage(path: string): string {
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".md")) return "markdown";
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".c") || path.endsWith(".h")) return "c";
  if (path.endsWith(".txt")) return "plaintext";
  return "plaintext";
}

type SaveStatus = "idle" | "saving" | "saved" | "error";

export default function AuthoringPage() {
  const params = useParams();
  const appId = params.appId as string;

  const [files, setFiles] = useState<FileEntry[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [skillContent, setSkillContent] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [versions, setVersions] = useState<VersionEntry[]>([]);
  const [deploying, setDeploying] = useState(false);
  const [deployMessage, setDeployMessage] = useState("");
  const [error, setError] = useState("");

  // Load files on mount
  useEffect(() => {
    loadFiles();
    loadVersions();
  }, [appId]);

  async function loadFiles() {
    try {
      const f = await listFiles(appId);
      setFiles(f);
      // Auto-select skill.md if exists
      if (!selectedPath && f.some((x) => x.path === "skill.md")) {
        selectFile("skill.md");
      }
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadVersions() {
    try {
      const v = await listVersions(appId);
      setVersions(v);
    } catch {}
  }

  async function selectFile(path: string) {
    try {
      const c = await readFile(appId, path);
      setSelectedPath(path);
      setContent(c);
      setValidationErrors([]);
      if (path === "skill.md") setSkillContent(c);
    } catch (e: any) {
      setError(e.message);
    }
  }

  // Auto-save with debounce
  const handleEditorChange = useCallback(
    (value: string | undefined) => {
      if (!selectedPath || value === undefined) return;
      setContent(value);
      if (selectedPath === "skill.md") setSkillContent(value);
      setSaveStatus("saving");
    },
    [selectedPath]
  );

  // Debounced save
  useEffect(() => {
    if (saveStatus !== "saving" || !selectedPath) return;

    const timeout = setTimeout(async () => {
      try {
        const result = await saveFile(appId, selectedPath, content);
        setValidationErrors(result.validation_errors);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("error");
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [saveStatus, content, selectedPath, appId]);

  async function handleDeploy() {
    setDeploying(true);
    setDeployMessage("");
    try {
      const result = await deployApp(appId);
      setDeployMessage(`Deployed v${result.version} at ${new Date(result.deployed_at).toLocaleTimeString("vi-VN")}`);
      loadVersions();
    } catch (e: any) {
      setDeployMessage(`Deploy failed: ${e.message}`);
    }
    setDeploying(false);
  }

  async function handleRollback(timestamp: string) {
    try {
      await rollback(appId, timestamp);
      await loadFiles();
      if (selectedPath) await selectFile(selectedPath);
      setDeployMessage(`Rolled back to ${timestamp}`);
    } catch (e: any) {
      setDeployMessage(`Rollback failed: ${e.message}`);
    }
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-57px)]">
        <div className="text-center">
          <div className="text-5xl mb-4">🔧</div>
          <h2 className="text-xl font-semibold text-gray-700">Không tìm thấy app</h2>
          <p className="text-gray-500 mt-2">{error}</p>
          <a href="/" className="text-blue-600 hover:underline mt-4 inline-block">
            ← Quay lại
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-57px)]">
      {/* LEFT PANEL (40%) — File tree + Editor */}
      <div className="w-[40%] flex flex-col border-r border-gray-200">
        {/* Top bar */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 bg-gray-50">
          <span className="text-sm font-semibold text-gray-700 truncate">
            {appId}
          </span>
          <div className="flex items-center gap-2">
            <span
              className={`text-xs ${
                saveStatus === "saving"
                  ? "text-yellow-600"
                  : saveStatus === "saved"
                    ? "text-green-600"
                    : saveStatus === "error"
                      ? "text-red-600"
                      : "text-gray-400"
              }`}
            >
              {saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved" : saveStatus === "error" ? "Error" : ""}
            </span>
          </div>
        </div>

        {/* File tree */}
        <div className="h-48 overflow-y-auto border-b border-gray-200">
          <FileTree files={files} selectedPath={selectedPath} onSelect={selectFile} />
        </div>

        {/* Validation errors */}
        {validationErrors.length > 0 && (
          <div className="px-3 py-2 bg-red-50 border-b border-red-200 text-xs text-red-700 max-h-24 overflow-y-auto">
            {validationErrors.map((err, i) => (
              <div key={i}>⚠ {err}</div>
            ))}
          </div>
        )}

        {/* Monaco editor */}
        <div className="flex-1">
          {selectedPath ? (
            <Editor
              language={getLanguage(selectedPath)}
              value={content}
              onChange={handleEditorChange}
              theme="vs-light"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                wordWrap: "on",
                tabSize: 2,
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-gray-400">
              Chọn một file để chỉnh sửa
            </div>
          )}
        </div>
      </div>

      {/* RIGHT PANEL (60%) — Chat test + deploy */}
      <div className="flex-1 flex flex-col">
        {/* Deploy bar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            <button
              onClick={handleDeploy}
              disabled={deploying || validationErrors.length > 0 || saveStatus === "saving"}
              className="px-4 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deploying ? "Deploying..." : "Deploy to Live"}
            </button>

            {/* Version dropdown */}
            {versions.length > 0 && (
              <select
                onChange={(e) => e.target.value && handleRollback(e.target.value)}
                className="text-xs border border-gray-300 rounded px-2 py-1"
                defaultValue=""
              >
                <option value="" disabled>
                  Rollback...
                </option>
                {versions.map((v) => (
                  <option key={v.timestamp} value={v.timestamp}>
                    v{v.version} — {v.timestamp}
                  </option>
                ))}
              </select>
            )}
          </div>

          {deployMessage && (
            <span
              className={`text-xs ${deployMessage.includes("failed") ? "text-red-600" : "text-green-600"}`}
            >
              {deployMessage}
            </span>
          )}
        </div>

        {/* Chat test panel */}
        <div className="flex-1">
          <ChatTestPanel appId={appId} skillContent={skillContent} />
        </div>
      </div>
    </div>
  );
}
