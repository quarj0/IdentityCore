import type { Metadata } from "next";
import { ArrowRight, FolderKanban, Plus } from "lucide-react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";
import { getStatusBadgeVariant, projects } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Projects" };

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Scope policies, keys, and endpoints into operational workspaces."
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            New project
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <Card key={project.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FolderKanban className="h-4 w-4" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{project.name}</CardTitle>
                    <CardDescription>{project.environment}</CardDescription>
                  </div>
                </div>
                <Badge variant={getStatusBadgeVariant(project.status)}>{project.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-4">
              <p className="text-sm leading-6 text-muted-foreground">{project.description}</p>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-lg bg-muted/50 p-3">
                  <div className="font-semibold text-foreground">{project.policies}</div>
                  <div className="text-xs text-muted-foreground">Policies</div>
                </div>
                <div className="rounded-lg bg-muted/50 p-3">
                  <div className="font-semibold text-foreground">{project.apiKeys}</div>
                  <div className="text-xs text-muted-foreground">API keys</div>
                </div>
                <div className="rounded-lg bg-muted/50 p-3">
                  <div className="font-semibold text-foreground">{project.webhooks}</div>
                  <div className="text-xs text-muted-foreground">Webhooks</div>
                </div>
              </div>
              <Button variant="outline" className="mt-auto justify-between">
                Open workspace
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
