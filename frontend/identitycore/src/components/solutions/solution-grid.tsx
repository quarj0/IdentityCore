import { solutions } from "@/data/solutions";
import { SolutionCard } from "./solutions-card"; 

export function SolutionGrid() {
  return (
    <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {solutions.map((solution) => (
        <SolutionCard key={solution.title} {...solution} />
      ))}
    </div>
  );
}