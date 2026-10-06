/** TypeScript mirrors of the backend Pydantic schemas (spec section 49). */

export type SentimentLabel = "Positive" | "Negative" | "Neutral" | "Mixed";
export type ReviewStatus = "VALID" | "UNCERTAIN" | "INVALID";
export type RelevanceLevel = "HIGH" | "MEDIUM" | "LOW";
export type DatasetDecision = "ACCEPT" | "ACCEPT WITH WARNING" | "REJECT";
export type AnalysisPhase =
  | "processing"
  | "completed"
  | "failed";

export interface AspectMention {
  category: string;
  sentiment: SentimentLabel;
  confidence: number;
}

export interface ReviewResult {
  id: number;
  original_text: string;
  normalized_text: string;
  word_count: number;
  review_probability: number;
  not_review_probability: number;
  review_status: ReviewStatus;
  relevance: number;
  relevance_level: RelevanceLevel;
  sentiment: SentimentLabel;
  confidence: number;
  positive_probability: number;
  negative_probability: number;
  neutral_probability: number;
  aspects: AspectMention[];
  suspicion_score: number;
  suspicious: boolean;
  suspicion_reasons: string[];
  contributing_terms: string[];
  duplicate: boolean;
  near_duplicate: boolean;
  duplicate_of: number | null;
}

export interface ReviewPage {
  analysis_id: string;
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  reviews: ReviewResult[];
}

export interface AspectSummary {
  aspect: string;
  mention_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;
  average_confidence: number;
  overall: SentimentLabel;
}

export interface ProsConsItem {
  aspect: string;
  percentage: number;
  mention_count: number;
  average_confidence: number;
  quotes: string[];
}

export interface TrustInfo {
  score: number;
  band: string;
  components: Record<string, number>;
}

export interface EmotionCount {
  emotion: string;
  count: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  matched: number;
  breakdown: { Positive: number; Negative: number; Neutral: number };
  quotes: { id: number; text: string; sentiment: SentimentLabel; confidence: number }[];
  analysis_id: string;
}

export interface QualityComponentScores {
  review_detection: number;
  opinion_density: number;
  feature_density: number;
  average_length: number;
  language_quality: number;
  dataset_diversity: number;
}

export interface QualityReport {
  total_rows: number;
  valid_reviews: number;
  uncertain_reviews: number;
  invalid_reviews: number;
  exact_duplicates: number;
  near_duplicates: number;
  average_word_count: number;
  opinion_density: number;
  feature_density: number;
  alphabetic_ratio: number;
  gibberish_ratio: number;
  excessive_symbol_ratio: number;
  language_quality: number;
  dataset_diversity: number;
  quality_score: number;
  dataset_decision: DatasetDecision;
  reasons: string[];
  component_scores: QualityComponentScores;
}

export interface Verdict {
  overall_sentiment: string;
  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;
  statement: string;
  strongest_positive_aspects: string[];
  main_negative_aspects: string[];
}

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
  mixed: number;
  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;
  mixed_percentage: number;
}

export interface ConfidenceHistogram {
  buckets: string[];
  counts: number[];
}

export interface AnalysisStatistics {
  reviews_analyzed: number;
  duplicates_removed: number;
  near_duplicates_detected: number;
  invalid_reviews: number;
  uncertain_reviews: number;
  suspicious_reviews: number;
  average_confidence: number;
  average_word_count: number;
  aspect_mentions_total: number;
  processing_ms: number;
}

export interface AnalysisSummary {
  analysis_id: string;
  created_at: string;
  source: string;
  filename: string | null;
  detected_column: string | null;
  status: string;
  sentiment: SentimentDistribution;
  confidence_histogram: ConfidenceHistogram;
  quality: QualityReport;
  aspects: AspectSummary[];
  pros: ProsConsItem[];
  cons: ProsConsItem[];
  most_discussed: ProsConsItem[];
  statistics: AnalysisStatistics;
  verdict: Verdict;
  trust: TrustInfo | null;
  emotions: EmotionCount[] | null;
}

export interface AnalysisResponse extends AnalysisSummary {
  reviews: ReviewResult[];
}

export interface AnalysisStatus {
  analysis_id: string;
  status: AnalysisPhase;
  progress: number;
  stage: string;
  error: { code: string; message: string } | null;
}

export interface ClassMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface ModelEvaluation {
  model_name: string;
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  macro_f1: number;
  weighted_f1: number;
  per_class: Record<string, ClassMetrics>;
  confusion_matrix: number[][];
}

export interface ModelInfo {
  task: string;
  selected_model: string;
  selection_metric: string;
  /** Candidate evaluations on the VALIDATION set (used for selection). */
  candidates: ModelEvaluation[];
  /** Single held-out TEST evaluation of the selected model. */
  selected_model_test_metrics: ModelEvaluation | null;
  classes: string[];
  training_rows: number;
  validation_rows: number | null;
  test_rows: number;
  tfidf_config: Record<string, unknown>;
  training_dataset: string;
  dataset_name: string | null;
  dataset_size: number | null;
  class_distribution: Record<string, number> | null;
  imbalance_handling: string | null;
  trained_at: string;
  model_version: string;
}

export interface ProductListItem {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  review_count: number;
  analysis_id: string | null;
  verdict?: string | null;
  trust?: number | null;
  quality?: number | null;
}

export interface CompareProduct {
  id: string;
  name: string;
  verdict?: string | null;
  trust?: number | null;
  quality?: number | null;
  positive_pct?: number | null;
  negative_pct?: number | null;
  review_count?: number | null;
}

export interface CompareResponse {
  success: boolean;
  products: CompareProduct[];
  aspects: {
    aspect: string;
    ratings: Record<string, string>;
    scores: Record<string, number>;
  }[];
}

export interface ApiErrorBody {
  success: false;
  error: { code: string; message: string; details?: Record<string, unknown> };
}
