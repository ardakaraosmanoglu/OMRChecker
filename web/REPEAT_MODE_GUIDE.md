# 🔁 Repeat Processing Mode - User Guide

## What is Repeat Processing Mode?

This special mode processes the **same OMR image multiple times** (2-10 times) and compares all results side-by-side to help you:

✅ **Test Consistency** - See if the OMR processing gives the same results every time
✅ **Identify Issues** - Spot questions with inconsistent detection
✅ **Quality Assurance** - Verify your template and settings are working reliably
✅ **Debug Problems** - Find which questions are problematic

## How to Use

### 1. Enable Repeat Mode

1. Open `web/index.html` in your browser
2. Select your OMR sheet image
3. Check the box: **🔁 Repeat Processing Mode**
4. A new section appears asking "Number of repetitions"

### 2. Set Repetition Count

Choose how many times to process the same image:
- Minimum: **2** (compare 2 results)
- Maximum: **10** (compare up to 10 results)
- Default: **3** (recommended for quick testing)

### 3. Click Process

Click **"🚀 Process OMR Sheet"** button.

The system will:
1. Process the same image multiple times
2. Show progress: "Processing attempt 1 of 3..."
3. Compare all results
4. Display in a comparison table

## Understanding the Results

### Summary Statistics

At the top, you'll see:

```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Total Runs  │   Total     │ Consistent  │Inconsistent │ Consistency │  Avg. Time  │
│             │  Questions  │             │             │    Rate     │   /Run      │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│      3      │     160     │     158     │      2      │    98.8%    │    0.75s    │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

- **Consistent (✅)**: Questions with identical answers across all runs
- **Inconsistent (❌)**: Questions with different answers in different runs
- **Consistency Rate**: Percentage of consistent questions (higher is better!)

### Comparison Table

Questions are displayed in order (q1, q2, q3...):

| Question | Run 1 | Run 2 | Run 3 | Status |
|----------|-------|-------|-------|--------|
| **q1**   | A     | A     | A     | ✅     |
| **q2**   | B     | B     | B     | ✅     |
| **q3**   | C     | C     | **D** | ❌     |
| **q4**   | -     | -     | -     | ✅     |
| **q5**   | A     | **B** | **C** | ❌     |

**Color Coding:**
- 🟢 **Normal rows**: All runs match (✅)
- 🟡 **Yellow highlighted rows**: Inconsistent results (❌)
- **Bold text**: Different answer from others

### Status Column

- ✅ **Green checkmark**: All runs produced the same answer (consistent)
- ❌ **Red X**: Different answers in different runs (inconsistent)

## Example Scenarios

### Scenario 1: Perfect Consistency ✅

```
Total Runs: 5
Consistent: 160 (100%)
Inconsistent: 0
Consistency Rate: 100%
```

**Interpretation:** Excellent! Your OMR processing is very reliable.

### Scenario 2: Mostly Consistent ⚠️

```
Total Runs: 3
Consistent: 155 (96.9%)
Inconsistent: 5 (3.1%)
Consistency Rate: 96.9%
```

**Interpretation:** Good, but check the 5 inconsistent questions. They might be:
- Lightly marked bubbles
- Smudged or unclear marks
- Edge cases for threshold detection

### Scenario 3: Many Inconsistencies ❌

```
Total Runs: 3
Consistent: 120 (75%)
Inconsistent: 40 (25%)
Consistency Rate: 75%
```

**Interpretation:** Problem detected! Possible causes:
- Template coordinates are slightly off
- Image quality is poor
- Threshold settings need adjustment
- Marker detection is unstable

## Tips for Best Results

### 1. When to Use Repeat Mode

✅ **Use when:**
- Testing a new template
- Validating your OMR setup
- Investigating why some answers seem wrong
- Quality assurance before processing many sheets

❌ **Don't use when:**
- You're confident in your setup
- Processing production data (just process once)
- You're in a hurry (it takes 3x longer!)

### 2. Choosing Repetition Count

- **2-3 repetitions**: Quick test, sufficient for most cases
- **5 repetitions**: More thorough testing
- **10 repetitions**: Maximum reliability check (but slowest)

### 3. Interpreting Inconsistencies

If you see inconsistent results:

1. **Check the image quality**
   - Is the image clear?
   - Good lighting?
   - No blur or shadows?

2. **Verify template accuracy**
   - Are bubble coordinates correct?
   - Does template match the physical sheet?

3. **Adjust threshold settings**
   - Try different `MIN_JUMP` values in config
   - Adjust `GLOBAL_PAGE_THRESHOLD_WHITE/BLACK`

4. **Enable auto-alignment**
   - Check "Enable auto-alignment" option
   - Helps with slight rotation/skew

## Common Patterns

### Pattern 1: Empty Bubbles Inconsistent

```
q45: -  -  A  ❌
q46: -  B  -  ❌
```

**Cause:** Threshold is borderline for these bubbles
**Solution:** Adjust threshold parameters

### Pattern 2: Multi-marked Questions Vary

```
q23: AB  A   AB  ❌
q24: CD  CDE CD  ❌
```

**Cause:** Multi-mark detection is unstable
**Solution:** Check bubble detection parameters

### Pattern 3: Specific Questions Always Different

```
q78: A  B  C  ❌
q79: D  E  A  ❌
```

**Cause:** Template coordinates may be wrong for these questions
**Solution:** Review and adjust template for these specific bubbles

## Advanced Usage

### Compare with Different Settings

Run repeat mode twice with different settings:

**Test 1:** Auto-align OFF, 3 repetitions
**Test 2:** Auto-align ON, 3 repetitions

Compare consistency rates to see which setting is more reliable!

### Identify Problematic Images

If consistency is low (<90%), this specific image may be:
- Poor quality
- Damaged/folded
- Incorrectly scanned

Try with different OMR sheet images to verify.

## Performance Notes

- Each run takes ~0.5-1 second
- 3 repetitions = ~2-3 seconds total
- 10 repetitions = ~5-10 seconds total

Processing time depends on:
- Image size and quality
- Number of questions
- Server performance
- Marker detection complexity

## Troubleshooting

### "Some processing attempts failed"

**Cause:** API error occurred during one or more runs
**Solution:** Check API server logs, try again

### All results identical but wrong

**Cause:** Processing is consistent but template/config is wrong
**Solution:** This is NOT a consistency issue - review your template setup

### Very slow processing

**Cause:** High repetition count (8-10) or large images
**Solution:** Reduce repetition count or use smaller images

## Summary

Repeat Processing Mode is a powerful diagnostic tool that helps you:

1. ✅ Verify OMR processing reliability
2. ✅ Identify problematic questions
3. ✅ Test different configurations
4. ✅ Build confidence in your setup

**Best Practice:** Before processing many OMR sheets, run repeat mode on a sample sheet to ensure >95% consistency!

---

**Happy Testing! 🎯**
