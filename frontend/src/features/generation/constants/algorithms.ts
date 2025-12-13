export const ALGORITHMS = [
    {
        key: "top_patent_countries",
        label: "Top Patent Countries",
        defaultParams: { top_n: 15 },
    },
    {
        key: "top_patent_inventors",
        label: "Top Patent Inventors",
        defaultParams: { top_n: 10 },
    },
    {
        key: "top_patent_applicants",
        label: "Top Patent Applicants",
        defaultParams: { top_n: 15 },
    },
    {
        key: "patent_evolution",
        label: "Patent Evolution",
        defaultParams: {},
    },
    {
        key: "patent_cumulative",
        label: "Patent Cumulative",
        defaultParams: {},
    },
    {
        key: "patent_trends_cumulative",
        label: "Patent Trends Cumulative",
        defaultParams: {},
    },
    {
        key: "patent_forecast",
        label: "Patent Forecast",
        defaultParams: {},
    },
    {
        key: "cpc_treemap",
        label: "CPC Treemap",
        defaultParams: { num_groups: 15 },
    },
] as const;

export type AlgorithmKey = (typeof ALGORITHMS)[number]["key"];

export interface AlgorithmConfig {
    algorithm_key: AlgorithmKey;
    algorithm_version: string;
    params: Record<string, unknown>;
    output_format: "png" | "svg" | "both";
}
