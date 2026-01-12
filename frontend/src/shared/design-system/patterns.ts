/**
 * UI/UX Component Patterns
 *
 * This file documents the established patterns for building consistent UI components.
 * Follow these patterns when creating new components to maintain design consistency.
 */

/**
 * =============================================================================
 * COLLAPSIBLE SECTIONS
 * =============================================================================
 *
 * Use for secondary information that users may want to see but isn't primary.
 *
 * Pattern:
 * - Default state: collapsed
 * - Toggle button: full-width clickable area
 * - Chevron icon: ChevronRight (collapsed) / ChevronDown (expanded)
 * - Subtle background on hover: hover:bg-muted/50
 *
 * Example usage: ActivityLog, secondary details panels
 *
 * ```tsx
 * <button
 *   onClick={() => setIsCollapsed(!isCollapsed)}
 *   className={cn(
 *     "w-full flex items-center justify-between p-3 rounded-lg transition-colors",
 *     "hover:bg-muted/50 text-left",
 *     isCollapsed ? "bg-transparent" : "bg-muted/30"
 *   )}
 * >
 *   <div className="flex items-center gap-2">
 *     {isCollapsed ? <ChevronRight /> : <ChevronDown />}
 *     <Icon />
 *     <span>Section Title</span>
 *     <Badge>{count}</Badge>
 *   </div>
 *   <span className="text-xs text-muted-foreground">
 *     {isCollapsed ? "Click to expand" : "Click to collapse"}
 *   </span>
 * </button>
 * ```
 */
export const collapsiblePattern = {
  defaultCollapsed: true,
  toggleClasses:
    "w-full flex items-center justify-between p-3 rounded-lg transition-colors hover:bg-muted/50 text-left",
  expandedClasses: "bg-muted/30",
  collapsedClasses: "bg-transparent",
};

/**
 * =============================================================================
 * STATUS HEADERS
 * =============================================================================
 *
 * Use for page/section headers that display status information.
 *
 * Pattern:
 * - Icon in colored circle (p-2 rounded-full bg-muted)
 * - Title with tracking-tight
 * - Status badges inline with title
 * - Action buttons aligned right
 *
 * ```tsx
 * <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b">
 *   <div className="flex items-start gap-3">
 *     <div className={`p-2 rounded-full bg-muted ${statusColor}`}>
 *       <StatusIcon className="h-5 w-5" />
 *     </div>
 *     <div>
 *       <h2 className="text-xl font-bold tracking-tight">Title</h2>
 *       <div className="flex items-center gap-2 mt-1">
 *         <Badge variant="...">Status</Badge>
 *       </div>
 *     </div>
 *   </div>
 *   <div className="flex gap-2">
 *     <Button>Action</Button>
 *   </div>
 * </div>
 * ```
 */
export const statusHeaderPattern = {
  iconContainerClasses: "p-2 rounded-full bg-muted",
  titleClasses: "text-xl font-bold tracking-tight",
  badgeContainerClasses: "flex items-center gap-2 mt-1",
  containerClasses:
    "flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b",
};

/**
 * =============================================================================
 * PROGRESS CARDS
 * =============================================================================
 *
 * Use for displaying progress with summary information.
 *
 * Pattern:
 * - Card wrapper with CardContent pt-6
 * - Status icon + title on left
 * - Percentage on right (text-2xl font-bold)
 * - Progress bar below
 * - Summary badges at bottom
 *
 * ```tsx
 * <Card>
 *   <CardContent className="pt-6">
 *     <div className="space-y-4">
 *       <div className="flex items-center justify-between">
 *         <div className="flex items-center gap-3">
 *           {getStatusIcon(status)}
 *           <div>
 *             <h3 className="font-semibold">Title</h3>
 *             <p className="text-sm text-muted-foreground">Subtitle</p>
 *           </div>
 *         </div>
 *         <span className="text-2xl font-bold">{progress}%</span>
 *       </div>
 *       <Progress value={progress} className="h-2" />
 *       <div className="flex gap-2 flex-wrap">
 *         <Badge>Summary item</Badge>
 *       </div>
 *     </div>
 *   </CardContent>
 * </Card>
 * ```
 */
export const progressCardPattern = {
  progressClasses: "text-2xl font-bold",
  progressBarClasses: "h-2",
  summaryContainerClasses: "flex gap-2 flex-wrap",
};

/**
 * =============================================================================
 * TASK ITEMS
 * =============================================================================
 *
 * Use for list items representing tasks/jobs with status.
 *
 * Pattern:
 * - Horizontal layout with icon, content, badges
 * - Border color changes based on status
 * - Background tint based on status
 * - Progress bar only shown when running
 *
 * ```tsx
 * <div
 *   className={cn(
 *     "flex items-center gap-3 p-3 rounded-lg border bg-card transition-colors",
 *     status === "RUNNING" && "border-primary/50 bg-primary/5",
 *     status === "SUCCESS" && "border-green-500/30 bg-green-500/5",
 *     status === "FAILED" && "border-red-500/30 bg-red-500/5"
 *   )}
 * >
 *   <div className="shrink-0">{icon}</div>
 *   <div className="flex-1 min-w-0">
 *     <div className="flex items-center justify-between gap-2">
 *       <span className="font-medium text-sm truncate">{title}</span>
 *       <Badge>{status}</Badge>
 *     </div>
 *     {status === "RUNNING" && <Progress className="h-1 mt-2" />}
 *   </div>
 * </div>
 * ```
 */
export const taskItemPattern = {
  baseClasses: "flex items-center gap-3 p-3 rounded-lg border bg-card transition-colors",
  runningClasses: "border-primary/50 bg-primary/5",
  successClasses: "border-green-500/30 bg-green-500/5",
  failedClasses: "border-red-500/30 bg-red-500/5",
  progressClasses: "h-1 mt-2",
};

/**
 * =============================================================================
 * TERMINAL LOG
 * =============================================================================
 *
 * Use for displaying log/event output with terminal aesthetic.
 *
 * Pattern:
 * - Dark background (slate-950 light, black dark)
 * - Monospace font (font-mono text-xs)
 * - Colored levels: ERROR=red-400, WARNING=amber-400, INFO=blue-400, DEBUG=slate-500
 * - Timestamp in muted color
 * - Auto-scroll with manual override detection
 *
 * ```tsx
 * <div className="overflow-y-auto font-mono text-xs bg-slate-950 dark:bg-black">
 *   {events.map((event) => (
 *     <div className={cn(
 *       "flex gap-2 py-1",
 *       event.level === "ERROR" && "bg-red-950/30 rounded px-2 -mx-2"
 *     )}>
 *       <span className="text-slate-500">{timestamp}</span>
 *       <span className={cn(
 *         event.level === "ERROR" && "text-red-400",
 *         event.level === "WARNING" && "text-amber-400",
 *         event.level === "INFO" && "text-blue-400",
 *       )}>
 *         [{event.level}]
 *       </span>
 *       <span className="text-slate-200">{event.message}</span>
 *     </div>
 *   ))}
 * </div>
 * ```
 */
export const terminalLogPattern = {
  containerClasses: "overflow-y-auto font-mono text-xs bg-slate-950 dark:bg-black",
  rowClasses: "flex gap-2 py-1",
  errorRowClasses: "bg-red-950/30 rounded px-2 -mx-2",
  timestampClasses: "text-slate-500 shrink-0",
  levelClasses: {
    ERROR: "text-red-400",
    WARNING: "text-amber-400",
    INFO: "text-blue-400",
    DEBUG: "text-slate-500",
  },
  messageClasses: "text-slate-200 break-all",
};

/**
 * =============================================================================
 * LOADING STATES
 * =============================================================================
 *
 * Use for full-area loading indicators.
 *
 * Pattern:
 * - Centered content
 * - Large spinner (h-12 w-12)
 * - Title + description text
 * - Subtle background
 *
 * ```tsx
 * <div className="flex flex-col items-center justify-center p-16 space-y-4 border rounded-lg bg-muted/20">
 *   <Loader2 className="h-12 w-12 animate-spin text-primary" />
 *   <div className="text-center">
 *     <p className="font-medium">Loading Title</p>
 *     <p className="text-sm text-muted-foreground">Description...</p>
 *   </div>
 * </div>
 * ```
 */
export const loadingStatePattern = {
  containerClasses:
    "flex flex-col items-center justify-center p-16 space-y-4 border rounded-lg bg-muted/20",
  spinnerClasses: "h-12 w-12 animate-spin text-primary",
  titleClasses: "font-medium",
  descriptionClasses: "text-sm text-muted-foreground",
};

/**
 * =============================================================================
 * ERROR ALERTS
 * =============================================================================
 *
 * Use for displaying errors with retry options.
 *
 * Pattern:
 * - Red border and background tint
 * - AlertCircle icon
 * - Title + description
 * - Action button (retry, dismiss)
 *
 * ```tsx
 * <div className="border border-red-500/50 bg-red-500/10 text-red-600 dark:text-red-400 p-4 rounded-lg flex items-start gap-3">
 *   <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
 *   <div className="flex-1 min-w-0">
 *     <h5 className="font-medium mb-1">Error Title</h5>
 *     <p className="text-sm break-words">{message}</p>
 *     <div className="mt-3">
 *       <Button onClick={onRetry} variant="outline" size="sm">Try Again</Button>
 *     </div>
 *   </div>
 * </div>
 * ```
 */
export const errorAlertPattern = {
  containerClasses:
    "border border-red-500/50 bg-red-500/10 text-red-600 dark:text-red-400 p-4 rounded-lg flex items-start gap-3",
  iconClasses: "h-5 w-5 mt-0.5 shrink-0",
  titleClasses: "font-medium mb-1",
  messageClasses: "text-sm break-words",
};

/**
 * =============================================================================
 * INFORMATION HIERARCHY (Progressive Disclosure)
 * =============================================================================
 *
 * Order content by priority:
 * 1. Primary: Always visible, main content (status, progress, results)
 * 2. Secondary: Visible but less prominent (task details)
 * 3. Tertiary: Collapsed by default (logs, debug info)
 *
 * Use visual separators (border-t, pt-6) between sections.
 * Use collapsible pattern for tertiary information.
 */
export const informationHierarchy = {
  primary: {
    description: "Main content always visible",
    examples: ["Status header", "Progress card", "Generated results"],
  },
  secondary: {
    description: "Supporting details, visible but de-emphasized",
    examples: ["Task list", "Configuration summary"],
  },
  tertiary: {
    description: "Technical details, collapsed by default",
    examples: ["Activity log", "Debug information", "Raw data"],
  },
};

/**
 * =============================================================================
 * BADGE USAGE
 * =============================================================================
 *
 * Badge variants and their semantic meaning:
 * - default: Success, completed, primary actions
 * - secondary: Neutral, in-progress, counts
 * - destructive: Errors, failures, warnings
 * - outline: Supplementary info, connection status
 *
 * Size: text-[10px] h-5 for compact badges in lists
 */
export const badgeUsage = {
  success: { variant: "default", icon: "CheckCircle2" },
  inProgress: { variant: "secondary", icon: "Loader2" },
  failed: { variant: "destructive", icon: "XCircle" },
  warning: { variant: "outline", className: "text-amber-600" },
  info: { variant: "outline", className: "text-blue-600" },
  live: { variant: "outline", className: "text-green-600", icon: "Wifi" },
  offline: { variant: "outline", className: "text-amber-600", icon: "WifiOff" },
};
