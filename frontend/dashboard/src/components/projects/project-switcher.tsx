"use client";

import { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@identitycore/ui";
import { dashboardApi, type Project } from "@/lib/dashboard-api";

const STORAGE_KEY = "identitycore.dashboard.project";

export function ProjectSwitcher() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    dashboardApi.projects().then(({ results }) => {
      setProjects(results);
      const saved = window.localStorage.getItem(STORAGE_KEY);
      const next = results.some((project) => project.id === saved)
        ? saved!
        : results.find((project) => project.is_default)?.id ?? results[0]?.id ?? "";
      setSelected(next);
      if (next) window.localStorage.setItem(STORAGE_KEY, next);
    }).catch(() => undefined);
  }, []);

  function change(value: string) {
    setSelected(value);
    window.localStorage.setItem(STORAGE_KEY, value);
    window.dispatchEvent(new CustomEvent("identitycore:project-change", { detail: value }));
  }

  if (!projects.length) return null;

  return (
    <Select value={selected} onValueChange={change}>
      <SelectTrigger className="h-9 w-44 rounded-xl" aria-label="Current project">
        <SelectValue placeholder="Select project" />
      </SelectTrigger>
      <SelectContent>
        {projects.map((project) => (
          <SelectItem key={project.id} value={project.id}>
            {project.name} · {project.environment}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
