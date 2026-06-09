'use client';
import { useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, ArrowRight, Play, Loader2, AlertCircle } from 'lucide-react';
import { fetchApi } from '@/lib/api';

/**
 * The result of a Digital Carbon Twin simulation run from the backend.
 */
interface SimulationResult {
  projected_emission: number;
  scenario: string;
  status: string;
}

/**
 * The display-ready result combining backend data with a static baseline
 * (baseline would ideally come from a user summary endpoint in a v2 API).
 */
interface DisplayResult {
  baseline: number;
  projected: number;
  scenario: string;
  saved: number;
}

/**
 * A predefined scenario that the user can select before running the simulation.
 */
interface Scenario {
  id: string;
  label: string;
  badge: string;
  category: string;
  reductionPercentage: number;
  days: number;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'reduce-ac',
    label: 'Reduce AC Usage by 20%',
    badge: '-15 kg CO₂',
    category: 'electricity',
    reductionPercentage: 20,
    days: 30,
  },
  {
    id: 'public-transport',
    label: 'Use Public Transport twice a week',
    badge: '-37 kg CO₂',
    category: 'transportation',
    reductionPercentage: 40,
    days: 30,
  },
  {
    id: 'vegetarian',
    label: 'Eat vegetarian 3 days a week',
    badge: '-22 kg CO₂',
    category: 'food',
    reductionPercentage: 43,
    days: 30,
  },
];

/** Placeholder baseline until a /carbon/summary endpoint is available. */
const BASELINE_PLACEHOLDER = 150.4;

export default function CarbonTwinPage() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(SCENARIOS[1].id);
  const [result, setResult] = useState<DisplayResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const selectedScenario = SCENARIOS.find((s) => s.id === selectedScenarioId)!;

  /**
   * Posts the selected scenario to /carbon/twin/simulate and renders the result.
   */
  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data: SimulationResult = await fetchApi('/carbon/twin/simulate', {
        method: 'POST',
        body: JSON.stringify({
          category_to_reduce: selectedScenario.category,
          reduction_percentage: selectedScenario.reductionPercentage,
          days_to_simulate: selectedScenario.days,
        }),
      });

      const saved = Math.max(0, BASELINE_PLACEHOLDER - data.projected_emission);

      setResult({
        baseline: BASELINE_PLACEHOLDER,
        projected: data.projected_emission,
        scenario: data.scenario,
        saved: Math.round(saved * 10) / 10,
      });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Simulation failed. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [selectedScenario]);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Digital Carbon Twin</h1>
        <p className="text-muted-foreground mt-1 text-lg">
          Simulate lifestyle changes and predict your future footprint.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ── Scenario Simulator Controls ──────────────────────────────── */}
        <Card className="shadow-sm border-blue-200 dark:border-blue-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" aria-hidden="true" />
              Scenario Simulator
            </CardTitle>
            <CardDescription>
              Select a lifestyle change below and run the simulation to see its impact.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Scenario selection list */}
            <fieldset>
              <legend className="sr-only">Choose a scenario to simulate</legend>
              <div className="space-y-3">
                {SCENARIOS.map((scenario) => {
                  const isSelected = scenario.id === selectedScenarioId;
                  return (
                    <label
                      key={scenario.id}
                      htmlFor={`scenario-${scenario.id}`}
                      className={[
                        'flex justify-between items-center p-4 rounded-lg border cursor-pointer transition-colors group',
                        isSelected
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'bg-card hover:border-blue-400 dark:hover:border-blue-600',
                      ].join(' ')}
                    >
                      <input
                        type="radio"
                        id={`scenario-${scenario.id}`}
                        name="simulation-scenario"
                        value={scenario.id}
                        checked={isSelected}
                        onChange={() => setSelectedScenarioId(scenario.id)}
                        className="sr-only"
                      />
                      <span
                        className={[
                          'font-medium',
                          isSelected
                            ? 'text-blue-700 dark:text-blue-300'
                            : 'group-hover:text-blue-600 dark:group-hover:text-blue-400',
                        ].join(' ')}
                      >
                        {scenario.label}
                      </span>
                      <Badge
                        className={
                          isSelected ? 'bg-blue-600 text-white' : undefined
                        }
                        variant={isSelected ? 'default' : 'outline'}
                      >
                        {scenario.badge}
                      </Badge>
                    </label>
                  );
                })}
              </div>
            </fieldset>

            {/* Error feedback */}
            {error && (
              <div role="alert" className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}

            <Button
              onClick={runSimulation}
              disabled={loading}
              aria-busy={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                  Running Simulation…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" aria-hidden="true" />
                  Run Simulation
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* ── Simulation Results ───────────────────────────────────────── */}
        {result && (
          <Card
            className="shadow-sm border-green-200 dark:border-green-900/50 animate-in zoom-in-95 duration-300"
            aria-live="polite"
            aria-label="Simulation results"
          >
            <CardHeader>
              <CardTitle>Simulation Results</CardTitle>
              <CardDescription>Projected footprint for next {selectedScenario.days} days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mt-4" role="presentation">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-1">Baseline</p>
                  <p
                    className="text-3xl font-bold text-gray-400"
                    aria-label={`Baseline: ${result.baseline} kg CO₂`}
                  >
                    {result.baseline}
                  </p>
                </div>

                <ArrowRight
                  className="w-8 h-8 text-green-500 mx-4 shrink-0"
                  aria-hidden="true"
                />

                <div className="text-center">
                  <p className="text-sm font-semibold text-green-600 mb-1">Projected</p>
                  <p
                    className="text-5xl font-bold text-green-600"
                    aria-label={`Projected: ${result.projected} kg CO₂`}
                  >
                    {result.projected}
                  </p>
                </div>
              </div>

              <div className="mt-8 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
                <p className="text-green-800 dark:text-green-300 font-medium">
                  By committing to this scenario, you could save an additional{' '}
                  <strong>{result.saved} kg CO₂</strong> this month!
                </p>
                <Button className="mt-4 bg-green-600 hover:bg-green-700">
                  Accept Challenge
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
