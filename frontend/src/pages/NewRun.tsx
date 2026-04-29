import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useRunStore } from "@/lib/run-store";
import type { RunConfig } from "@/lib/types";

export default function NewRun() {
  const navigate = useNavigate();
  const createRun = useRunStore(s => s.createRun);

  const [name, setName] = useState("untitled run");
  const [aiMode, setAiMode] = useState<RunConfig["aiMode"]>("big_bang");
  const [playMode, setPlayMode] = useState<RunConfig["playMode"]>("manual");
  const [temperature, setTemperature] = useState(0.85);
  const [shockProb, setShockProb] = useState(0.05);
  const [seed, setSeed] = useState(19980201);
  const [model, setModel] = useState<RunConfig["model"]>("gemini-2.5-flash");
  const [notes, setNotes] = useState("");

  const submit = () => {
    const run = createRun({ name, aiMode, playMode, temperature, randomShockProbability: shockProb, seed, model, notes });
    navigate(`/runs/${run.id}`);
  };

  return (
    <div className="min-h-screen scanlines">
      <header className="border-b border-border">
        <div className="container py-6 flex items-center justify-between">
          <Link to="/runs" className="font-mono text-xs uppercase tracking-widest text-muted-foreground hover:text-primary">
            ← runs
          </Link>
          <div className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            configurar nova simulação
          </div>
        </div>
      </header>

      <main className="container py-10 max-w-2xl">
        <h1 className="font-serif text-4xl text-amber mb-2">novo contrafactual</h1>
        <p className="font-mono text-xs text-muted-foreground mb-8">
          cada parâmetro define um possível mundo · seed determina reprodutibilidade
        </p>

        <div className="panel p-8 space-y-7">
          <Field label="nome">
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full bg-elevated border border-border px-3 py-2 font-mono text-sm focus:border-primary outline-none"
            />
          </Field>

          <Field label="ai_mode" hint="trajetória de capacidade ao longo dos 58 turnos">
            <RadioRow value={aiMode} onChange={(v) => setAiMode(v as RunConfig["aiMode"])} options={[
              { v: "big_bang", l: "big bang", d: "salto inicial em S1/1998" },
              { v: "accelerated_curve", l: "accelerated curve", d: "rampa progressiva" },
            ]} />
          </Field>

          <Field label="play_mode" hint="quem decide quando avançar turno">
            <RadioRow value={playMode} onChange={(v) => setPlayMode(v as RunConfig["playMode"])} options={[
              { v: "manual", l: "manual", d: "" },
              { v: "auto", l: "auto", d: "" },
              { v: "hybrid", l: "hybrid", d: "" },
            ]} />
          </Field>

          <Field label="temperature" hint="afeta apenas a prosa do cronista — nunca os números do motor">
            <Slider value={temperature} min={0.3} max={1.2} step={0.05} onChange={setTemperature} format={v => v.toFixed(2)} />
          </Field>

          <Field label="random_shock_probability" hint="chance, por turno, de choque exógeno fora dos âncoras">
            <Slider value={shockProb} min={0} max={0.2} step={0.01} onChange={setShockProb} format={v => v.toFixed(2)} />
          </Field>

          <Field label="seed">
            <div className="flex gap-2">
              <input
                type="number"
                value={seed}
                onChange={e => setSeed(Number(e.target.value))}
                className="flex-1 bg-elevated border border-border px-3 py-2 font-mono text-sm focus:border-primary outline-none tabular-nums"
              />
              <button
                onClick={() => setSeed(Math.floor(Math.random() * 99999999))}
                className="px-4 py-2 border border-border font-mono text-xs uppercase hover:border-primary/60"
                type="button"
              >
                aleatorizar
              </button>
            </div>
          </Field>

          <Field label="model">
            <select
              value={model}
              onChange={e => setModel(e.target.value as RunConfig["model"])}
              className="w-full bg-elevated border border-border px-3 py-2 font-mono text-sm focus:border-primary outline-none"
            >
              <option value="gemini-2.5-flash">gemini-2.5-flash</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro</option>
            </select>
          </Field>

          <Field label="notes" hint="a hipótese sociológica que essa run testa">
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              className="w-full bg-elevated border border-border px-3 py-2 font-mono text-xs focus:border-primary outline-none resize-none"
              placeholder="ex: e se a regulação europeia tivesse vindo dez anos antes?"
            />
          </Field>

          <div className="pt-2">
            <button
              onClick={submit}
              className="w-full font-mono text-sm uppercase tracking-widest px-6 py-4 border border-primary text-primary bg-primary/5 hover:bg-primary/15 glow-cyan"
            >
              ▶ iniciar simulação
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <label className="metric-label">{label}</label>
        {hint && <span className="font-mono text-[10px] text-muted-foreground/80 italic">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

function RadioRow({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { v: string; l: string; d: string }[] }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {options.map(o => {
        const active = o.v === value;
        return (
          <button
            key={o.v}
            onClick={() => onChange(o.v)}
            type="button"
            className={`px-4 py-2 border font-mono text-xs uppercase tracking-wider transition-colors ${
              active ? "border-primary text-primary bg-primary/10" : "border-border text-muted-foreground hover:border-primary/40"
            }`}
          >
            {o.l}
            {o.d && <span className="block text-[9px] normal-case tracking-normal opacity-60 mt-0.5">{o.d}</span>}
          </button>
        );
      })}
    </div>
  );
}

function Slider({ value, min, max, step, onChange, format }: { value: number; min: number; max: number; step: number; onChange: (v: number) => void; format: (v: number) => string }) {
  return (
    <div className="space-y-2">
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-primary"
      />
      <div className="flex justify-between font-mono text-[10px] text-muted-foreground tabular-nums">
        <span>{format(min)}</span>
        <span className="text-primary">{format(value)}</span>
        <span>{format(max)}</span>
      </div>
    </div>
  );
}
