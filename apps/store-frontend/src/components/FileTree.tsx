/**
 * File tree component for the authoring IDE.
 * Shows app folder structure, highlights selected file.
 */

"use client";

import type { FileEntry } from "@/lib/authoring-api";

interface FileTreeProps {
  files: FileEntry[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}

// Build a tree from flat file list
interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
  size?: number;
}

function buildTree(files: FileEntry[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split("/");
    let current = root;

    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      const isLast = i === parts.length - 1;
      const path = parts.slice(0, i + 1).join("/");

      let node = current.find((n) => n.name === name);
      if (!node) {
        node = {
          name,
          path,
          isDir: !isLast,
          children: [],
          size: isLast ? file.size : undefined,
        };
        current.push(node);
      }
      current = node.children;
    }
  }

  return root;
}

function FileIcon({ name, isDir }: { name: string; isDir: boolean }) {
  if (isDir) return <span className="text-yellow-500">📁</span>;
  if (name.endsWith(".json")) return <span className="text-yellow-600">{ }</span>;
  if (name.endsWith(".md")) return <span className="text-blue-500">M↓</span>;
  if (name.endsWith(".py")) return <span className="text-green-600">🐍</span>;
  if (name.endsWith(".png") || name.endsWith(".jpg")) return <span>🖼</span>;
  return <span className="text-gray-400">📄</span>;
}

function TreeItem({
  node,
  depth,
  selectedPath,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const isSelected = node.path === selectedPath;

  return (
    <div>
      <button
        onClick={() => !node.isDir && onSelect(node.path)}
        className={`w-full text-left px-2 py-1 text-sm flex items-center gap-1.5 rounded hover:bg-gray-100 ${
          isSelected ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-700"
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        disabled={node.isDir}
      >
        <FileIcon name={node.name} isDir={node.isDir} />
        <span className="truncate">{node.name}</span>
      </button>
      {node.children.map((child) => (
        <TreeItem
          key={child.path}
          node={child}
          depth={depth + 1}
          selectedPath={selectedPath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

export function FileTree({ files, selectedPath, onSelect }: FileTreeProps) {
  const tree = buildTree(files);

  if (files.length === 0) {
    return <div className="p-4 text-sm text-gray-400">No files</div>;
  }

  return (
    <div className="py-1">
      {tree.map((node) => (
        <TreeItem
          key={node.path}
          node={node}
          depth={0}
          selectedPath={selectedPath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
