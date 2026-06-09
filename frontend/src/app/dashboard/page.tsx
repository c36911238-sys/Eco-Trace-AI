'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import type { Metadata } from 'next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Camera, Zap, Car, Apple, ShoppingBag, Trash, Loader2 } from 'lucide-react';
import { fetchApi } from '@/lib/api';

/**
 * A single SHAP explanation value returned by the backend AI engine.
 */
interface SHAPExplanation {
  feature: string;
  impact: number;
  description: string;
}

/**
 * AI insights payload from GET /carbon/insights.
 */
interface InsightsResponse {
  predicted_emission: number;
  target_date: string;
  explanations: SHAPExplanation[];
}

/** Maps emission category names to their visual icon components. */
const CATEGORY_ICON_MAP: Record<string, React.ReactNode> = {
  Transportation: <Car className="w-4 h-4 text-blue-500" aria-hidden="true" />,
  Electricity: <Zap className="w-4 h-4 text-yellow-500" aria-hidden="true" />,
  Food: <Apple className="w-4 h-4 text-green-500" aria-hidden="true" />,
  Shopping: <ShoppingBag className="w-4 h-4 text-purple-500" aria-hidden="true" />,
  Waste: <Trash className="w-4 h-4 text-gray-500" aria-hidden="true" />,
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export default function DashboardPage() {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /** Fetches AI insights from the backend on mount. */
  const loadInsights = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: InsightsResponse = await fetchApi('/carbon/insights');
      setInsights(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch AI insights.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInsights();
  }, [loadInsights]);

  /**
   * Handles receipt image selection and upload.
   * Validates file type and size client-side before posting to the backend.
   */
  const handleReceiptUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setUploadError(null);
      setUploadSuccess(false);

      // Client-side validation
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        setUploadError('Only JPEG, PNG, and WebP images are supported.');
        return;
      }
      if (file.size > MAX_UPLOAD_BYTES) {
        setUploadError('File size must be under 5 MB.');
        return;
      }

      setUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', file);

        const token =
          typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

        const response = await fetch(`${BASE_URL}/carbon/receipt`, {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
          // ⚠️ Do NOT set Content-Type manually — browser must set the multipart boundary.
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail ?? 'Receipt upload failed.');
        }

        setUploadSuccess(true);
        // Refresh insights to reflect the newly created log
        await loadInsights();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Receipt upload failed.';
        setUploadError(message);
      } finally {
        setUploading(false);
        // Reset input so same file can be re-uploaded
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    },
    [loadInsights],
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, Eco Hero!</h1>
          <p className="text-muted-foreground mt-1 text-lg">
            Here is your carbon footprint breakdown.
          </p>
        </div>

        {/* Receipt upload — fully functional with validation feedback */}
        <div className="flex flex-col items-end gap-1">
          <label
            htmlFor="receipt-upload"
            className={[
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium shadow-sm transition-all',
              'outline-none focus-within:ring-2 focus-within:ring-green-500 focus-within:ring-offset-2',
              uploading
                ? 'bg-green-400 cursor-not-allowed text-white'
                : 'bg-green-600 hover:bg-green-700 text-white cursor-pointer',
            ].join(' ')}
            aria-label="Upload a receipt to auto-log carbon emissions"
          >
            {uploading ? (
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
            ) : (
              <Camera className="w-5 h-5" aria-hidden="true" />
            )}
            <span>{uploading ? 'Processing…' : 'Scan Receipt'}</span>
            <input
              id="receipt-upload"
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="sr-only"
              onChange={handleReceiptUpload}
              disabled={uploading}
              aria-describedby="upload-feedback"
            />
          </label>

          {/* Upload feedback — visible to all users including screen readers */}
          <div id="upload-feedback" role="status" aria-live="polite" className="text-xs">
            {uploadError && <span className="text-red-500">{uploadError}</span>}
            {uploadSuccess && (
              <span className="text-green-600 font-medium">
                ✓ Receipt logged successfully!
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ── Stats Overview ───────────────────────────────────────────────── */}
      <section aria-label="Carbon savings summary">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-green-500/20 shadow-sm bg-gradient-to-br from-white to-green-50/50 dark:from-zinc-900 dark:to-green-900/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Total Saved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-green-600 dark:text-green-500">
                124{' '}
                <span className="text-xl font-normal text-muted-foreground">kg CO₂</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2 font-medium flex items-center gap-1">
                <span className="text-green-600" aria-label="12% increase">↑ 12%</span> from last month
              </p>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Current Level
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <div className="text-4xl font-bold" aria-label="Level 4">
                  Level 4
                </div>
                <Badge
                  variant="secondary"
                  className="bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                >
                  Seedling
                </Badge>
              </div>
              <Progress
                value={65}
                className="h-2 mt-4"
                aria-label="Progress to next level: 65%"
              />
              <p className="text-xs text-muted-foreground mt-2">35 points to next level</p>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Community Impact
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold">
                4,592{' '}
                <span className="text-xl font-normal text-muted-foreground">Trees</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Saved collectively by EcoTrace users this week.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ── SHAP AI Explanations ─────────────────────────────────────────── */}
      <section aria-label="AI-powered carbon insights">
        <h2 className="text-2xl font-bold mb-4">Why is your footprint high?</h2>
        <Card className="shadow-sm border border-orange-200 dark:border-orange-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-500" aria-hidden="true" />
              Advanced AI Insights
            </CardTitle>
            <CardDescription>
              Powered by Real-time SHAP Values (Scikit-Learn Random Forest)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {loading && (
              <div
                role="status"
                aria-live="polite"
                className="flex items-center gap-2 text-sm text-muted-foreground"
              >
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Running Random Forest calculations…</span>
              </div>
            )}

            {error && (
              <div role="alert" className="text-sm text-red-500 font-medium">
                Error loading AI Insights: {error}
              </div>
            )}

            {!loading && !error && insights?.explanations.map((exp: SHAPExplanation, i: number) => (
              <div key={`${exp.feature}-${i}`} className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 font-medium">
                    {CATEGORY_ICON_MAP[exp.feature] ?? (
                      <Zap className="w-4 h-4 text-gray-500" aria-hidden="true" />
                    )}
                    <span>{exp.feature}</span>
                  </div>
                  <span className="text-sm font-bold text-orange-600">
                    {exp.impact}% impact
                  </span>
                </div>
                <Progress
                  value={exp.impact}
                  className="h-2 bg-gray-100 dark:bg-gray-800"
                  aria-label={`${exp.feature} impact: ${exp.impact}%`}
                />
                <p className="text-sm text-muted-foreground mt-1">{exp.description}</p>
              </div>
            ))}

            {!loading && !error && insights?.explanations.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No significant insights yet. Start logging your activities to see your AI breakdown.
              </p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
