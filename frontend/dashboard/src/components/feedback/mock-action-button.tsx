"use client";

import { Button } from "@identitycore/ui";
import { useToast } from "@identitycore/ui";

export function MockActionButton({ label }: { label: string }) {
  const { toast } = useToast();

  return (
    <Button
      type="button"
      className="rounded-xl"
      onClick={() =>
        toast({
          title: "Action completed",
          description: `${label} was simulated successfully.`,
        })
      }
    >
      {label}
    </Button>
  );
}
