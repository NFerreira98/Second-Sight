// frontend/src/app/page.tsx
import { redirect } from "next/navigation";

export default function HomePage() {
  // Instantly redirect users from the root to the dashboard
  redirect("/dashboard");
}