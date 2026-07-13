package dkma.monster

import android.app.Activity
import android.content.Context
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.LifecycleResumeEffect

/**
 * DkmaWizard — a drop-in Jetpack Compose "keep me alive" wizard UI kit.
 *
 * It renders a friendly, OEM-aware checklist on top of [DkmaMonster]:
 *   - a header explaining WHY (device brand + honest note that toggles are manual)
 *   - one card per required step, each opening the exact vendor settings screen
 *   - progress + a "done" state
 *
 * The wizard cannot read most vendor toggles (no API), so each step is marked
 * done by the user after they return from Settings. The battery-optimization
 * step is the one thing we CAN verify, and it auto-checks on resume.
 *
 * Usage (in an Activity or nav destination):
 *
 *     setContent {
 *         MaterialTheme {
 *             DkmaWizardScreen(onFinish = { finish() })
 *         }
 *     }
 *
 * Requires Compose Material3 + androidx.lifecycle:lifecycle-runtime-compose.
 * No other dependencies.
 */

/** UI status for a single wizard step. */
enum class StepUiState { PENDING, OPENED, DONE }

/** Observable state holder the composables render from. */
class DkmaWizardState(private val appContext: Context) {
    val steps: List<DkmaMonster.Step> = DkmaMonster.stepsFor(appContext)
    val statuses = mutableStateListOf<StepUiState>().apply {
        repeat(steps.size) { add(StepUiState.PENDING) }
    }
    var batteryExempt by mutableStateOf(
        DkmaMonster.isIgnoringBatteryOptimizations(appContext)
    )
    /** Authoritative autostart state where readable (MIUI/HyperOS). */
    var autostart by mutableStateOf(DkmaMonster.autostartState(appContext))

    val romLabel: String = DkmaMonster.romLabel()
    val oemLabel: String = DkmaMonster.currentOem().label

    val doneCount: Int get() = statuses.count { it == StepUiState.DONE }
    val total: Int get() = steps.size
    val allDone: Boolean get() = doneCount == total

    fun open(ctx: Context, index: Int) {
        DkmaMonster.openStep(ctx, steps[index])
        if (statuses[index] == StepUiState.PENDING) statuses[index] = StepUiState.OPENED
    }

    fun markDone(index: Int) { statuses[index] = StepUiState.DONE }
    fun toggleDone(index: Int) {
        statuses[index] =
            if (statuses[index] == StepUiState.DONE) StepUiState.OPENED
            else StepUiState.DONE
    }

    fun refreshBattery(ctx: Context) {
        batteryExempt = DkmaMonster.isIgnoringBatteryOptimizations(ctx)
        autostart = DkmaMonster.autostartState(ctx)
        // If we can PROVE autostart is now enabled, auto-tick that step.
        if (autostart == DkmaAutostart.State.ENABLED) {
            val i = steps.indexOfFirst { it.id == "autostart" }
            if (i >= 0 && statuses[i] != StepUiState.DONE) statuses[i] = StepUiState.DONE
        }
    }

    /** True only when autostart is authoritatively proven enabled. */
    val autostartVerified: Boolean get() = autostart == DkmaAutostart.State.ENABLED
}

@Composable
fun rememberDkmaWizardState(): DkmaWizardState {
    val ctx = LocalContext.current.applicationContext
    return remember { DkmaWizardState(ctx) }
}

/**
 * The full-screen wizard. Drop it into any Compose host.
 * @param onFinish called when the user taps Done/Finish.
 */
@Composable
fun DkmaWizardScreen(
    modifier: Modifier = Modifier,
    state: DkmaWizardState = rememberDkmaWizardState(),
    onFinish: () -> Unit = {},
) {
    val ctx = LocalContext.current

    // Re-check the battery-optimization exemption whenever we return to the app.
    LifecycleResumeEffect(Unit) {
        state.refreshBattery(ctx)
        onPauseOrDispose { }
    }

    Surface(modifier = modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            WizardHeader(state)

            BatteryOptimizationCard(
                exempt = state.batteryExempt,
                onFix = { DkmaMonster.requestIgnoreBatteryOptimizations(ctx) }
            )

            state.steps.forEachIndexed { i, step ->
                StepCard(
                    index = i + 1,
                    step = step,
                    status = state.statuses[i],
                    verified = step.id == "autostart" && state.autostartVerified,
                    onOpen = { state.open(ctx, i) },
                    onToggleDone = { state.toggleDone(i) },
                )
            }

            FinishBar(state = state, onFinish = onFinish)

            Text(
                "Autostart, MIUI/OEM optimizations and protected-app lists have no " +
                "public API, so these toggles are set by you \u2014 we just take you " +
                "straight to each screen. Reference: dontkillmyapp.com",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }
}

@Composable
private fun WizardHeader(state: DkmaWizardState) {
    val progress by animateFloatAsState(
        targetValue = if (state.total == 0) 1f else state.doneCount / state.total.toFloat(),
        label = "progress"
    )
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            "Keep this app running",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )
        Text(
            "Your ${state.romLabel} device (${state.oemLabel}) limits background " +
            "apps aggressively. Complete these quick steps so notifications, syncs " +
            "and alarms keep working.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { progress },
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp))
        )
        Text(
            "${state.doneCount} of ${state.total} steps done",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun BatteryOptimizationCard(exempt: Boolean, onFix: () -> Unit) {
    val container =
        if (exempt) MaterialTheme.colorScheme.secondaryContainer
        else MaterialTheme.colorScheme.errorContainer
    Card(colors = CardDefaults.cardColors(containerColor = container)) {
        Row(
            Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusDot(done = exempt)
            Column(Modifier.weight(1f)) {
                Text(
                    if (exempt) "Battery optimization: exempt \u2713"
                    else "Battery optimization: needs attention",
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    if (exempt) "This app is already excluded from Doze. Nice."
                    else "Tap Fix and choose \u201cAllow\u201d / \u201cDon't optimize.\u201d",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            if (!exempt) {
                Button(onClick = onFix) { Text("Fix") }
            }
        }
    }
}

@Composable
private fun StepCard(
    index: Int,
    step: DkmaMonster.Step,
    status: StepUiState,
    verified: Boolean = false,
    onOpen: () -> Unit,
    onToggleDone: () -> Unit,
) {
    val done = status == StepUiState.DONE || verified
    OutlinedCard {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                StepBadge(index = index, done = done)
                Text(
                    step.title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f)
                )
                if (verified) {
                    AssistChip(
                        onClick = {},
                        label = { Text("Verified") },
                        leadingIcon = {
                            Icon(Icons.Default.Check, contentDescription = null,
                                 modifier = Modifier.size(16.dp))
                        }
                    )
                }
            }
            if (step.hint.isNotBlank()) {
                Text(
                    step.hint,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = onOpen, modifier = Modifier.weight(1f)) {
                    Text(if (status == StepUiState.PENDING) "Open settings" else "Open again")
                    Icon(Icons.Default.KeyboardArrowRight, contentDescription = null)
                }
                if (done) {
                    OutlinedButton(onClick = onToggleDone) { Text("Undo") }
                } else {
                    Button(onClick = onToggleDone) {
                        Icon(Icons.Default.Check, contentDescription = null)
                        Spacer(Modifier.width(4.dp))
                        Text("Done")
                    }
                }
            }
        }
    }
}

@Composable
private fun FinishBar(state: DkmaWizardState, onFinish: () -> Unit) {
    AnimatedVisibility(visible = true) {
        Button(
            onClick = onFinish,
            enabled = true,
            modifier = Modifier.fillMaxWidth().height(52.dp)
        ) {
            Text(if (state.allDone) "All set \u2014 Finish" else "Finish for now")
        }
    }
}

@Composable
private fun StepBadge(index: Int, done: Boolean) {
    val bg = if (done) MaterialTheme.colorScheme.primary
             else MaterialTheme.colorScheme.surfaceVariant
    val fg = if (done) MaterialTheme.colorScheme.onPrimary
             else MaterialTheme.colorScheme.onSurfaceVariant
    Box(
        Modifier.size(32.dp).clip(CircleShape).background(bg),
        contentAlignment = Alignment.Center
    ) {
        if (done) Icon(Icons.Default.Check, contentDescription = null, tint = fg)
        else Text("$index", color = fg, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun StatusDot(done: Boolean) {
    val c = if (done) Color(0xFF2E7D32) else Color(0xFFC62828)
    Box(Modifier.size(14.dp).clip(CircleShape).background(c))
}

/* ---------------------------------------------------------------------------
 * Optional: launch the wizard as a bottom sheet from anywhere.
 * ------------------------------------------------------------------------- */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DkmaWizardBottomSheet(onDismiss: () -> Unit) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        DkmaWizardScreen(
            modifier = Modifier.fillMaxHeight(0.9f),
            onFinish = onDismiss
        )
    }
}
