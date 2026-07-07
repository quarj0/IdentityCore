import { Check } from "lucide-react";

const useCases = [
  "Customer onboarding",
  "Student enrollment",
  "Employee verification",
  "Government services",
  "Access workflows",
  "Risk operations",
];

export function UseCaseGrid() {
  return (
    <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {useCases.map((item) => (
        <div
          key={item}
          className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <Check className="h-5 w-5 text-blue-600" />
          <span className="text-sm font-medium">{item}</span>
        </div>
      ))}
    </div>
  );
}
