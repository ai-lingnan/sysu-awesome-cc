# Time Filter Guide

Time range is a **parameter** passed to all analysis agents, not a separate agent set.

## Time Filter Values

| User Selection | Filter Value | Description |
|---------------|--------------|-------------|
| 全量分析 (All) | `from all available history` | No date restriction |
| 近月分析 (30d) | `from the last 30 days only` | Filter to recent month |
| 本周分析 (7d) | `from the last 7 days only` | Filter to recent week |

## How to Apply

When constructing agent prompts, replace `[TIME_FILTER]` placeholder with the appropriate filter text.

### Example Transformation

**Template:**
```
Analyze Claude Code chat archives [TIME_FILTER]:
1. Read session files matching the time criteria
...
```

**After applying 7-day filter:**
```
Analyze Claude Code chat archives from the last 7 days only:
1. Read session files matching the time criteria
...
```

## Archive Path Hints by Time

| Time Range | Primary Search Paths |
|------------|---------------------|
| All | `[ARCHIVE_ROOT]/projects/` (all subdirectories) |
| 30d | `[ARCHIVE_ROOT]/timeline/YYYY-MM/` (current and previous month) |
| 7d | `[ARCHIVE_ROOT]/timeline/YYYY-MM/` (current month, last 7 days) |

## Output File Naming by Time

| Time Range | Output Pattern | Example |
|------------|----------------|---------|
| All | `CC全量[分析类型]_YYYYMMDD.md` | `CC全量多维度分析_20250105.md` |
| 30d | `CC_Monthly_[Type]_YYYYMM.md` | `CC_Monthly_MultiDim_202501.md` |
| 7d | `CC_Weekly_[Type]_YYYYMMDD.md` | `CC_Weekly_MultiDim_20250105.md` |

## Report Summary Prefix by Time

| Time Range | Summary Prefix |
|------------|----------------|
| All | `基于全部历史数据分析` |
| 30d | `基于近30天数据分析` |
| 7d | `基于近7天数据分析` |
