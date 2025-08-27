using OmnimonModuleEditor.Models;
using System.IO;

namespace OmnimonModuleEditor.docgenerators
{
    internal class HomeGenerator
    {
        public static void GenerateHomePage(string docPath, Module module, string modulePath)
        {
            string template = GeneratorUtils.GetTemplateContent("home.html");
            string content = template
                // Always replace longer tokens first to avoid conflicts
                .Replace("#MODULEADVENTUREMODECLASS", module?.AdventureMode == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULEADVENTUREMODE", module?.AdventureMode == true ? "Yes" : "No")
                .Replace("#MODULECAREMEATWEIGHTGAINCLASS", GetIntegerCssClass(module?.CareMeatWeightGain))
                .Replace("#MODULECAREMEATWEIGHTGAIN", GetIntegerDisplayValue(module?.CareMeatWeightGain))
                .Replace("#MODULECAREMEATHUNGERGAINCLASS", GetFloatCssClass(module?.CareMeatHungerGain))
                .Replace("#MODULECAREMEATHUNGERGAIN", GetFloatDisplayValue(module?.CareMeatHungerGain))
                .Replace("#MODULECAREMEATCAREMISTAKETIMECLASS", GetIntegerCssClass(module?.CareMeatCareMistakeTime))
                .Replace("#MODULECAREMEATCAREMISTAKETIME", GetIntegerDisplayValue(module?.CareMeatCareMistakeTime))
                .Replace("#MODULECAREOVERFEEDTIMERCLASS", GetIntegerCssClass(module?.CareOverfeedTimer))
                .Replace("#MODULECAREOVERFEEDTIMER", GetIntegerDisplayValue(module?.CareOverfeedTimer))
                .Replace("#MODULECARECONDITIONHEARTCLASS", module?.CareConditionHeart == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULECARECONDITIONHEART", module?.CareConditionHeart == true ? "Yes" : "No")
                .Replace("#MODULECARECANEATSLEEPINGCLASS", module?.CareCanEatSleeping == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULECARECANEATSLEEPING", module?.CareCanEatSleeping == true ? "Yes" : "No")
                .Replace("#MODULECAREBACKTOSLEEPTIMECLASS", GetIntegerCssClass(module?.CareBackToSleepTime))
                .Replace("#MODULECAREBACKTOSLEEPTIME", GetIntegerDisplayValue(module?.CareBackToSleepTime))
                .Replace("#MODULECARESHAKENEEGGCLASS", module?.CareEnableShakenEgg == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULECARESHAKENEGG", module?.CareEnableShakenEgg == true ? "Yes" : "No")
                .Replace("#MODULECAREFLUSHDETURBANCESLEEPCLASS", module?.CareFlushDisturbanceSleep == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULECAREFLUSHDETURBANCESLEEP", module?.CareFlushDisturbanceSleep == true ? "Yes" : "No")

                // Care Protein
                .Replace("#MODULECAREPROTEINWEIGHTGAINCLASS", GetIntegerCssClass(module?.CareProteinWeightGain))
                .Replace("#MODULECAREPROTEINWEIGHTGAIN", GetIntegerDisplayValue(module?.CareProteinWeightGain))
                .Replace("#MODULECAREPROTEINSTRENGTHGAINCLASS", GetFloatCssClass(module?.CareProteinStrenghGain))
                .Replace("#MODULECAREPROTEINSTRENGTHGAIN", GetFloatDisplayValue(module?.CareProteinStrenghGain))
                .Replace("#MODULECAREPROTEINDPGAINCLASS", GetIntegerCssClass(module?.CareProteinDpGain))
                .Replace("#MODULECAREPROTEINDPGAIN", GetIntegerDisplayValue(module?.CareProteinDpGain))
                .Replace("#MODULECAREPROTEINCAREMISTAKETIMECLASS", GetIntegerCssClass(module?.CareProteinCareMistakeTime))
                .Replace("#MODULECAREPROTEINCAREMISTAKETIME", GetIntegerDisplayValue(module?.CareProteinCareMistakeTime))
                .Replace("#MODULECAREPROTEINOVERDOSEMAXCLASS", GetIntegerCssClass(module?.CareProteinOverdoseMax))
                .Replace("#MODULECAREPROTEINOVERDOSEMAX", GetIntegerDisplayValue(module?.CareProteinOverdoseMax))
                .Replace("#MODULECAREPROTEINPENALTYCLASS", GetIntegerCssClass(module?.CareProteinPenalty ?? 10))
                .Replace("#MODULECAREPROTEINPENALTY", GetIntegerDisplayValue(module?.CareProteinPenalty ?? 10))
                .Replace("#MODULECARESDISTURBANCEPENALTYCLASS", GetIntegerCssClass(module?.CareDisturbancePenaltyMax))
                .Replace("#MODULECARESDISTURBANCEPENALTY", GetIntegerDisplayValue(module?.CareDisturbancePenaltyMax))

                // Care Sleep
                .Replace("#MODULECARESLEEPCAREMISTAKECLASS", GetIntegerCssClass(module?.CareSleepCareMistakeTimer))
                .Replace("#MODULECARESLEEPCAREMISTAKE", GetIntegerDisplayValue(module?.CareSleepCareMistakeTimer))

                // Training
                .Replace("#MODULETRAININGSTRENGTHGAINWINCLASS", GetIntegerCssClass(module?.TrainingStrenghGainWin))
                .Replace("#MODULETRAININGSTRENGTHGAINWIN", GetIntegerDisplayValue(module?.TrainingStrenghGainWin))
                .Replace("#MODULETRAININGSTRENGTHGAINLOSECLASS", GetIntegerCssClass(module?.TrainingStrenghGainLose))
                .Replace("#MODULETRAININGSTRENGTHGAINLOSE", GetIntegerDisplayValue(module?.TrainingStrenghGainLose))
                .Replace("#MODULETRAININGSTRENGMULTIPLIERCLASS", GetFloatCssClass(module?.TrainingStrenghMultiplier))
                .Replace("#MODULETRAININGSTRENGMULTIPLIER", GetFloatDisplayValue(module?.TrainingStrenghMultiplier))
                .Replace("#MODULETRAININGWEIGHTWINCLASS", GetIntegerCssClass(module?.TrainingWeightWin))
                .Replace("#MODULETRAININGWEIGHTWIN", GetIntegerDisplayValue(module?.TrainingWeightWin))
                .Replace("#MODULETRAININGWEIGHTLOSECLASS", GetIntegerCssClass(module?.TrainingWeightLose))
                .Replace("#MODULETRAININGWEIGHTLOSE", GetIntegerDisplayValue(module?.TrainingWeightLose))
                .Replace("#MODULETRAITEDEGGLEVELCLASS", GetIntegerCssClass(module?.TraitedEggStartingLevel))
                .Replace("#MODULETRAITEDEGGLEVEL", GetIntegerDisplayValue(module?.TraitedEggStartingLevel))
                .Replace("#MODULEREVERSEATKFRAMESCLASS", module?.ReverseAtkFrames == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULEREVERSEATKFRAMES", module?.ReverseAtkFrames == true ? "Yes" : "No")

                // Battle
                .Replace("#MODULEBATTLEBASESICKCHANCEWINCLASS", GetIntegerCssClass(module?.BattleBaseSickChanceWin))
                .Replace("#MODULEBATTLEBASESICKCHANCEWIN", GetIntegerDisplayValue(module?.BattleBaseSickChanceWin))
                .Replace("#MODULEBATTLEBASESICKCHANCELOSECLASS", GetIntegerCssClass(module?.BattleBaseSickChanceLose))
                .Replace("#MODULEBATTLEBASESICKCHANCELOSE", GetIntegerDisplayValue(module?.BattleBaseSickChanceLose))
                .Replace("#MODULEBATTLEATTRIBUTEADVANTAGECLASS", GetIntegerCssClass(module?.BattleAtributeAdvantage))
                .Replace("#MODULEBATTLEATTRIBUTEADVANTAGE", GetIntegerDisplayValue(module?.BattleAtributeAdvantage))
                .Replace("#MODULEBATTLEGLOBALHITPOINTSCLASS", GetIntegerCssClass(module?.BattleGlobalHitPoints))
                .Replace("#MODULEBATTLEGLOBALHITPOINTS", GetIntegerDisplayValue(module?.BattleGlobalHitPoints))
                .Replace("#MODULEBATTLESEQUENTIALROUNDSCLASS", module?.BattleSequentialRounds == true ? "boolean-true" : "boolean-false")
                .Replace("#MODULEBATTLESEQUENTIALROUNDS", module?.BattleSequentialRounds == true ? "Yes" : "No")

                // Death
                .Replace("#MODULEDEATHMAXINJURIESCLASS", GetIntegerCssClass(module?.DeathMaxInjuries))
                .Replace("#MODULEDEATHMAXINJURIES", GetIntegerDisplayValue(module?.DeathMaxInjuries))
                .Replace("#MODULEDEATHCAREMISTAKECLASS", GetIntegerCssClass(module?.DeathCareMistake))
                .Replace("#MODULEDEATHCAREMISTAKE", GetIntegerDisplayValue(module?.DeathCareMistake))
                .Replace("#MODULEDEATHSICKTIMERCLASS", GetIntegerCssClass(module?.DeathSickTimer))
                .Replace("#MODULEDEATHSICKTIMER", GetIntegerDisplayValue(module?.DeathSickTimer))
                .Replace("#MODULEDEATHHUNGERMISTAKECLASS", GetIntegerCssClass(module?.DeathHungerTimer))
                .Replace("#MODULEDEATHHUNGERMISTAKE", GetIntegerDisplayValue(module?.DeathHungerTimer))
                .Replace("#MODULEDEATHSTARVATIONCOUNTCLASS", GetIntegerCssClass(module?.DeathStarvationCount))
                .Replace("#MODULEDEATHSTARVATIONCOUNT", GetIntegerDisplayValue(module?.DeathStarvationCount))
                .Replace("#MODULEDEATHSTRENGTHTIMERCLASS", GetIntegerCssClass(module?.DeathStrengthTimer))
                .Replace("#MODULEDEATHSTRENGTHTIMER", GetIntegerDisplayValue(module?.DeathStrengthTimer))
                .Replace("#MODULEDEATHSTAGE45MISTAKECLASS", GetIntegerCssClass(module?.DeathStage45Mistake))
                .Replace("#MODULEDEATHSTAGE45MISTAKE", GetIntegerDisplayValue(module?.DeathStage45Mistake))
                .Replace("#MODULEDEATHSTAGE67MISTAKECLASS", GetIntegerCssClass(module?.DeathStage67Mistake))
                .Replace("#MODULEDEATHSTAGE67MISTAKE", GetIntegerDisplayValue(module?.DeathStage67Mistake))
                .Replace("#MODULEDEATHSAVEBYBPRESSCLASS", GetBooleanOrIntegerClass(module?.DeathSaveByBPress))
                .Replace("#MODULEDEATHSAVEBYBPRESS", GetBooleanOrIntegerDisplay(module?.DeathSaveByBPress))
                .Replace("#MODULEDEATHSAVEBYSHAKECLASS", GetBooleanOrIntegerClass(module?.DeathSaveByShake))
                .Replace("#MODULEDEATHSAVEBYSHAKE", GetBooleanOrIntegerDisplay(module?.DeathSaveByShake))
                .Replace("#MODULEDEATHOLDAGECLASS", GetIntegerCssClass(module?.DeathOldAge))
                .Replace("#MODULEDEATHOLDAGE", GetIntegerDisplayValue(module?.DeathOldAge))

                // Vital Values - NEW
                .Replace("#MODULEVITALVALUEBASECLASS", GetIntegerCssClass(module?.VitalValueBase))
                .Replace("#MODULEVITALVALUEBASE", GetIntegerDisplayValue(module?.VitalValueBase))
                .Replace("#MODULEVITALVALUELOSSCLASS", GetIntegerCssClass(module?.VitalValueLoss))
                .Replace("#MODULEVITALVALUELOSS", GetIntegerDisplayValue(module?.VitalValueLoss))

                // General fields (always last to avoid conflicts)
                .Replace("#MODULENAME", module?.Name ?? "Unknown Module")
                .Replace("#MODULEVERSION", module?.Version ?? "1.0")
                .Replace("#MODULEDESCRIPTION", module?.Description ?? "No description available")
                .Replace("#MODULEAUTHOR", module?.Author ?? "Unknown Author")
                .Replace("#MODULEFILEFORMAT", module?.NameFormat ?? "Unknown")
                .Replace("#MODULERULESET", module?.Ruleset ?? "Unknown");

            string logoPath = Path.Combine(modulePath, "logo.png");
            if (File.Exists(logoPath))
            {
                File.Copy(logoPath, Path.Combine(docPath, "logo.png"), true);
            }

            File.WriteAllText(Path.Combine(docPath, "home.html"), content);
        }

        /// <summary>
        /// Returns the string value of an integer
        /// </summary>
        private static string GetIntegerDisplayValue(int? value)
        {
            return (value ?? 0).ToString();
        }

        /// <summary>
        /// Returns CSS class for integer values. 0 = "boolean-false" (red), anything else = "boolean-true" (green)
        /// </summary>
        private static string GetIntegerCssClass(int? value)
        {
            int actualValue = value ?? 0;
            return actualValue == 0 ? "boolean-false" : "";
        }

        /// <summary>
        /// Converts integer values to boolean display text. 0 = "No", anything else = "Yes"
        /// </summary>
        private static string GetBooleanOrIntegerDisplay(int? value)
        {
            if (!value.HasValue) return "No";
            return value.Value == 0 ? "No" : "Yes";
        }

        /// <summary>
        /// Converts integer values to boolean CSS class. 0 = "boolean-false", anything else = "boolean-true"
        /// </summary>
        private static string GetBooleanOrIntegerClass(int? value)
        {
            if (!value.HasValue) return "boolean-false";
            return value.Value == 0 ? "boolean-false" : "boolean-true";
        }

        private static string GetFloatDisplayValue(float? value)
        {
            return (value ?? 0).ToString("0.##");
        }

        private static string GetFloatCssClass(float? value)
        {
            float actualValue = value ?? 0;
            return actualValue == 0 ? "boolean-false" : "";
        }
    }
}
