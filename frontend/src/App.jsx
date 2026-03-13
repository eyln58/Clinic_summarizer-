import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Activity, FileText, RefreshCw, ShieldCheck } from 'lucide-react'

const EMPTY_RESULT = 'Your approved summary will appear here after the review is complete.'

function getOverallStatus(activeNode, result, error) {
  if (error) return 'Error'
  if (activeNode === 'generator') return 'Writing summary'
  if (activeNode === 'critic') return 'Reviewing summary'
  if (activeNode === 'loop') return 'Revision requested'
  if (activeNode === 'printing' || result) return 'Approved'
  return 'Ready'
}

function getSummaryStatus(activeNode, result) {
  if (activeNode === 'generator') return 'Writing'
  if (activeNode === 'critic' || activeNode === 'loop' || activeNode === 'printing' || result) return 'Complete'
  return 'Idle'
}

function getReviewStatus(activeNode, result) {
  if (activeNode === 'critic') return 'Reviewing'
  if (activeNode === 'loop') return 'Needs revision'
  if (activeNode === 'printing' || result) return 'Approved'
  return 'Idle'
}

function getBarWidth(activeNode, result, node) {
  if (node === 'generator') {
    if (activeNode === 'generator') return '68%'
    if (activeNode === 'critic' || activeNode === 'loop' || activeNode === 'printing' || result) return '100%'
    return '12%'
  }

  if (activeNode === 'critic') return '72%'
  if (activeNode === 'loop') return '38%'
  if (activeNode === 'printing' || result) return '100%'
  return '10%'
}

function StatusBadge({ label, value, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    red: 'bg-rose-50 text-rose-700 border-rose-200',
  }

  return (
    <div className={`rounded-2xl border px-4 py-3 ${tones[tone]}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] opacity-80">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  )
}

function WorkerCard({ icon: Icon, title, status, progressTone, progressWidth, accentClass }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <div className="flex items-start gap-3">
        <div className={`flex h-8 w-8 items-center justify-center rounded-xl ${accentClass}`}>
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[15px] font-semibold text-slate-900">{title}</div>
          <div className="mt-0.5 text-[13px] text-slate-500">{status}</div>
        </div>
      </div>

      <div className="mt-1">
        <div className="mb-0.5 flex items-center justify-between text-[10px] font-medium uppercase tracking-[0.12em] text-slate-500">
          <span>Progress</span>
          <span>{status}</span>
        </div>
        <div className="h-2.5 rounded-full bg-slate-100">
          <div
            className={`h-2.5 rounded-full transition-[width] duration-300 ease-out ${progressTone}`}
            style={{ width: progressWidth }}
          />
        </div>
      </div>
    </div>
  )
}

function App() {
  const [input, setInput] = useState('')
  const [activeNode, setActiveNode] = useState('idle')
  const [result, setResult] = useState('')
  const [iteration, setIteration] = useState(0)
  const [isPrinting, setIsPrinting] = useState(false)
  const [error, setError] = useState('')
  const [activityLog, setActivityLog] = useState([
    'System ready. Enter symptoms to start the summary workflow.',
  ])

  const latestDraftRef = useRef('')

  const appendLog = (message) => {
    setActivityLog((current) => [message, ...current].slice(0, 4))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!input.trim() || activeNode === 'generator' || activeNode === 'critic') {
      return
    }

    latestDraftRef.current = ''
    setResult('')
    setIteration(0)
    setIsPrinting(false)
    setError('')
    setActiveNode('generator')
    setActivityLog(['Summary request sent.', 'System ready. Enter symptoms to start the summary workflow.'])

    try {
      const response = await fetch('http://localhost:8000/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom: input }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Network response failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let done = false

      while (!done) {
        const chunk = await reader.read()
        done = chunk.done
        buffer += decoder.decode(chunk.value || new Uint8Array(), { stream: !done })

        const packets = buffer.split('\n\n')
        buffer = packets.pop() ?? ''

        for (const packet of packets) {
          if (!packet.startsWith('data: ')) {
            continue
          }

          const payload = JSON.parse(packet.slice(6))
          const stateData = payload.state ?? {}

          if (payload.event === 'ERROR') {
            throw new Error(payload.data || 'Unknown stream error')
          }

          if (payload.event !== 'NODE_UPDATE') {
            continue
          }

          if (payload.node === 'generator') {
            if (stateData.draft) {
              latestDraftRef.current = stateData.draft
            }
            setIteration((prev) => prev + 1)
            setActiveNode('critic')
            appendLog('Summary draft created and sent for review.')
          }

          if (payload.node === 'critic') {
            if (stateData.approved) {
              setResult(latestDraftRef.current)
              setIsPrinting(true)
              setActiveNode('printing')
              appendLog('Quality review approved the summary.')
            } else {
              setActiveNode('loop')
              appendLog('Quality review requested a revision.')
            }
          }
        }
      }
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Unexpected error'
      setError(message)
      setActiveNode('error')
      appendLog(`Error: ${message}`)
    }
  }

  const handleRetry = () => {
    latestDraftRef.current = ''
    setInput('')
    setResult('')
    setIteration(0)
    setIsPrinting(false)
    setError('')
    setActiveNode('idle')
    setActivityLog(['System ready. Enter symptoms to start the summary workflow.'])
  }

  const overallStatus = getOverallStatus(activeNode, result, error)
  const summaryStatus = getSummaryStatus(activeNode, result)
  const reviewStatus = getReviewStatus(activeNode, result)
  const latestLog = activityLog[0] ?? 'System ready. Enter symptoms to start the summary workflow.'
  const statusPanelTitle =
    activeNode === 'idle' && !result && !error ? 'Activity Log' : 'Current Status'

  return (
    <div className="bg-slate-100 text-slate-900 lg:h-[100dvh] lg:overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:flex lg:h-full lg:flex-col lg:px-8">
        <header className="mb-4 rounded-3xl border border-slate-200 bg-white px-5 py-5 shadow-sm lg:flex-none">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">Pneumatic Agent</h1>
              <p className="mt-1 text-sm text-slate-600">
                Enter patient symptoms, generate a concise clinical summary, and run a quality check before approval.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <StatusBadge label="Overall Status" value={overallStatus} tone={error ? 'red' : result ? 'green' : 'blue'} />
              <StatusBadge label="Review Count" value={`${iteration}`} tone="amber" />
              <StatusBadge label="Output" value={result ? 'Ready' : 'Pending'} tone={result ? 'green' : 'slate'} />
            </div>
          </div>
        </header>

        <div className="grid gap-4 lg:min-h-0 lg:flex-1 lg:grid-cols-12">
          <section className="lg:col-span-4 lg:min-h-0">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:flex lg:h-full lg:min-h-0 lg:flex-col">
              <div className="mb-4 lg:flex-none">
                <h2 className="text-xl font-semibold text-slate-900">Patient Input</h2>
                <p className="mt-1 text-sm text-slate-500">Describe the symptoms in plain language.</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col">
                <textarea
                  className="h-64 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-base text-slate-800 outline-none transition focus:border-blue-300 focus:bg-white focus:ring-4 focus:ring-blue-100 lg:min-h-0 lg:flex-1"
                  placeholder="Example: Headache for two days, nausea, sensitivity to light."
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  disabled={activeNode === 'generator' || activeNode === 'critic'}
                />

                <button
                  type="submit"
                  disabled={!input.trim() || activeNode === 'generator' || activeNode === 'critic'}
                  className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  Create Summary
                </button>
              </form>

              <div className="mt-3 text-sm text-slate-500 lg:flex-none">
                The system keeps reviewing the draft until it is approved or the review limit is reached.
              </div>
            </div>
          </section>

          <section className="lg:col-span-4 lg:min-h-0">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:flex lg:h-full lg:min-h-0 lg:flex-col">
              <div className="mb-4 lg:flex-none">
                <h2 className="text-xl font-semibold text-slate-900">Processing</h2>
                <p className="mt-1 text-sm text-slate-500">Track the writing and quality review steps.</p>
              </div>

              <div className="space-y-1 lg:flex-none">
                <WorkerCard
                  icon={FileText}
                  title="Summary Writer"
                  status={summaryStatus}
                  progressTone="bg-gradient-to-r from-blue-500 to-sky-400"
                  progressWidth={getBarWidth(activeNode, result, 'generator')}
                  accentClass="bg-blue-50 text-blue-700"
                />
                <WorkerCard
                  icon={ShieldCheck}
                  title="Quality Checker"
                  status={reviewStatus}
                  progressTone="bg-gradient-to-r from-amber-500 to-yellow-400"
                  progressWidth={getBarWidth(activeNode, result, 'critic')}
                  accentClass="bg-amber-50 text-amber-700"
                />
              </div>

              <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 lg:flex-none">
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <Activity className="h-4 w-4" />
                  {statusPanelTitle}
                </div>
                <div
                  className="flex min-h-12 items-center rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-600 shadow-sm"
                  aria-live="polite"
                >
                  <motion.div
                    key={latestLog}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className="line-clamp-2"
                  >
                    {latestLog}
                  </motion.div>
                </div>
              </div>
            </div>
          </section>

          <section className="lg:col-span-4 lg:min-h-0">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:flex lg:h-full lg:min-h-0 lg:flex-col">
              <div className="mb-4 lg:flex-none">
                <h2 className="text-xl font-semibold text-slate-900">Approved Output</h2>
                <p className="mt-1 text-sm text-slate-500">Only the approved summary is shown here.</p>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={result ? 'result' : 'empty'}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className="lg:min-h-0 lg:flex-1"
                  >
                    {result ? (
                      <div className="space-y-3 lg:flex lg:h-full lg:flex-col">
                        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 lg:flex-none">
                          Summary approved
                        </div>
                        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-[15px] leading-7 text-slate-700 lg:min-h-0 lg:flex-1">
                          {result}
                        </div>
                      </div>
                    ) : (
                      <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 text-center text-sm leading-6 text-slate-500 lg:h-full lg:min-h-0">
                        {error ? `An error occurred: ${error}` : EMPTY_RESULT}
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>

              <div className="mt-4 flex gap-3 lg:flex-none">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="inline-flex h-12 flex-1 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  <RefreshCw className="h-4 w-4" />
                  Reset
                </button>
              </div>

              <div className="mt-3 text-sm text-slate-500 lg:flex-none">
                {isPrinting || result ? 'The latest approved version is displayed.' : 'No approved summary yet.'}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default App
