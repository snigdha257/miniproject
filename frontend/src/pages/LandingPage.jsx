import { Link } from 'react-router-dom'
import { Shield, Sparkles, Lock, FileText } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-12 lg:px-8">
        <header className="flex flex-col gap-6 text-center">
          <div className="inline-flex items-center gap-3 rounded-full border border-slate-700 bg-slate-900/80 px-4 py-2 text-sm text-slate-300">
            <Shield className="h-5 w-5 text-indigo-400" />
            Secure document privacy and masking engine
          </div>
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              Enterprise document privacy made simple.
            </h1>
            <p className="mt-6 text-base leading-8 text-slate-300 sm:text-lg sm:leading-9">
              Upload documents, detect sensitive entities, mask them safely, review privacy risk, and recover secure content with a key.
            </p>
          </div>
          <Link
            to="/login"
            className="mx-auto rounded-full bg-indigo-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400"
          >
            Get started
          </Link>
        </header>

        <section className="mt-16 grid gap-6 md:grid-cols-3">
          {[
            {
              title: 'AI-driven entity detection',
              description: 'Detect names, IDs, phone numbers, emails, and more across text and documents.',
              icon: Sparkles,
            },
            {
              title: 'Privacy scoring & risk report',
              description: 'Understand document exposure at a glance with scorecards and risk levels.',
              icon: Lock,
            },
            {
              title: 'Secure masking workflow',
              description: 'Mask sensitive items and recover them later with an encrypted key.',
              icon: FileText,
            },
          ].map((feature) => (
            <article key={feature.title} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-black/20">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-300">
                <feature.icon className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-semibold text-white">{feature.title}</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">{feature.description}</p>
            </article>
          ))}
        </section>

        <section className="mt-20 grid gap-8 lg:grid-cols-2 lg:items-center">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl shadow-black/20">
            <h2 className="text-2xl font-semibold text-white">Built for data protection teams</h2>
            <p className="mt-4 text-slate-400 leading-7">
              Keep sensitive information out of exports, automate secure masking pipelines, and monitor document risk from one centralized dashboard.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-full bg-slate-800 px-4 py-2 text-sm text-slate-300">PDF</span>
              <span className="rounded-full bg-slate-800 px-4 py-2 text-sm text-slate-300">DOCX</span>
              <span className="rounded-full bg-slate-800 px-4 py-2 text-sm text-slate-300">Text</span>
              <span className="rounded-full bg-slate-800 px-4 py-2 text-sm text-slate-300">Secure Mode</span>
            </div>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl shadow-black/20">
            <h3 className="text-sm uppercase tracking-[0.24em] text-indigo-400">Fast workflow</h3>
            <p className="mt-4 text-base leading-7 text-slate-300">
              Visit the dashboard, upload or paste text, mask in place, and review privacy results without leaving the app.
            </p>
            <div className="mt-8 grid gap-4 text-slate-400">
              <div className="rounded-3xl bg-slate-950/80 p-4">Upload documents or paste text</div>
              <div className="rounded-3xl bg-slate-950/80 p-4">Choose standard or secure masking</div>
              <div className="rounded-3xl bg-slate-950/80 p-4">View analysis, unmask with keys, and track history</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
