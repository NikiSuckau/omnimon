using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace OmnipetModuleEditor.Models
{
    public class Module
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }
        [JsonPropertyName("version")]
        public string Version { get; set; }
        [JsonPropertyName("description")]
        public string Description { get; set; }
        [JsonPropertyName("author")]
        public string Author { get; set; }

        [JsonPropertyName("category")]
        public string Category { get; set; } = "Custom";

        [JsonPropertyName("name_format")]
        public string NameFormat { get; set; }

        [JsonPropertyName("ruleset")]
        public string Ruleset { get; set; }

        [JsonPropertyName("adventure_mode")]
        public bool AdventureMode { get; set; }

        // High Definition Sprites - NEW
        [JsonPropertyName("high_definition_sprites")]
        public bool HighDefinitionSprites { get; set; } = false;

        // Visible Stats - NEW
        [JsonPropertyName("visible_stats")]
        public string VisibleStats { get; set; }

        // Care Meat
        [JsonPropertyName("care_meat_weight_gain")]
        public int CareMeatWeightGain { get; set; }

        [JsonPropertyName("care_meat_hunger_gain")]
        public float CareMeatHungerGain { get; set; }

        [JsonPropertyName("care_meat_care_mistake_time")]
        public int CareMeatCareMistakeTime { get; set; }

        [JsonPropertyName("care_overfeed_timer")]
        public int CareOverfeedTimer { get; set; }

        [JsonPropertyName("care_condition_heart")]
        public bool CareConditionHeart { get; set; }

        [JsonPropertyName("care_can_eat_sleeping")]
        public bool CareCanEatSleeping { get; set; }

        [JsonPropertyName("care_back_to_sleep_time")]
        public int CareBackToSleepTime { get; set; }

        [JsonPropertyName("care_enable_shaken_egg")]
        public bool CareEnableShakenEgg { get; set; }

        [JsonPropertyName("care_flush_disturbance_sleep")]
        public bool CareFlushDisturbanceSleep { get; set; } = true;

        // Care Protein
        [JsonPropertyName("care_protein_weight_gain")]
        public int CareProteinWeightGain { get; set; }

        [JsonPropertyName("care_protein_strengh_gain")]
        public float CareProteinStrenghGain { get; set; }

        [JsonPropertyName("care_protein_dp_gain")]
        public int CareProteinDpGain { get; set; }

        [JsonPropertyName("care_protein_care_mistake_time")]
        public int CareProteinCareMistakeTime { get; set; }

        [JsonPropertyName("care_protein_overdose_max")]
        public int CareProteinOverdoseMax { get; set; }

        [JsonPropertyName("care_protein_penalty")]
        public int? CareProteinPenalty { get; set; }

        [JsonPropertyName("care_disturbance_penalty_max")]
        public int CareDisturbancePenaltyMax { get; set; }

        // Care Sleep
        [JsonPropertyName("care_sleep_care_mistake_timer")]
        public int CareSleepCareMistakeTimer { get; set; }

        // Training
        [JsonPropertyName("training_effort_gain")]
        public int TrainingEffortGain { get; set; }

        [JsonPropertyName("training_strengh_gain_win")]
        public int TrainingStrenghGainWin { get; set; }

        [JsonPropertyName("training_strengh_gain_lose")]
        public int TrainingStrenghGainLose { get; set; }

        [JsonPropertyName("training_strengh_multiplier")]
        public float TrainingStrenghMultiplier { get; set; } = 1.0f;

        [JsonPropertyName("training_weight_win")]
        public int TrainingWeightWin { get; set; }

        [JsonPropertyName("training_weight_lose")]
        public int TrainingWeightLose { get; set; }

        [JsonPropertyName("traited_egg_starting_level")]
        public int TraitedEggStartingLevel { get; set; }

        [JsonPropertyName("reverse_atk_frames")]
        public bool ReverseAtkFrames { get; set; }

        // Battle
        [JsonPropertyName("battle_base_sick_chance_win")]
        public int BattleBaseSickChanceWin { get; set; }

        [JsonPropertyName("battle_base_sick_chance_lose")]
        public int BattleBaseSickChanceLose { get; set; }

        // Add alias property for compatibility
        [JsonPropertyName("battle_base_sick_chance_loose")]
        public int BattleBaseSickChanceLoose 
        { 
            get { return BattleBaseSickChanceLose; } 
            set { BattleBaseSickChanceLose = value; } 
        }

        [JsonPropertyName("battle_atribute_advantage")]
        public int BattleAtributeAdvantage { get; set; }

        [JsonPropertyName("battle_global_hit_points")]
        public int BattleGlobalHitPoints { get; set; }

        [JsonPropertyName("battle_sequential_rounds")]
        public bool BattleSequentialRounds { get; set; }

        // Death
        [JsonPropertyName("death_max_injuries")]
        public int DeathMaxInjuries { get; set; }

        [JsonPropertyName("death_care_mistake")]
        public int DeathCareMistake { get; set; }

        [JsonPropertyName("death_sick_timer")]
        public int DeathSickTimer { get; set; }

        [JsonPropertyName("death_hunger_timer")]
        public int DeathHungerTimer { get; set; }

        [JsonPropertyName("death_starvation_count")]
        public int DeathStarvationCount { get; set; }

        [JsonPropertyName("death_strength_timer")]
        public int DeathStrengthTimer { get; set; }

        [JsonPropertyName("death_stage45_mistake")]
        public int DeathStage45Mistake { get; set; }

        [JsonPropertyName("death_stage67_mistake")]
        public int DeathStage67Mistake { get; set; }

        [JsonPropertyName("death_save_by_b_press")]
        public int DeathSaveByBPress { get; set; }

        [JsonPropertyName("death_save_by_shake")]
        public int DeathSaveByShake { get; set; }

        // Death by old age - NEW
        [JsonPropertyName("death_old_age")]
        public int DeathOldAge { get; set; }

        // Vital Values Settings - NEW
        [JsonPropertyName("vital_value_base")]
        public int VitalValueBase { get; set; }

        [JsonPropertyName("vital_value_loss")]
        public int VitalValueLoss { get; set; }

        // Item Boost Settings - NEW
        [JsonPropertyName("hp_max_item_boost")]
        public int HpMaxItemBoost { get; set; } = 0;

        [JsonPropertyName("atk_max_item_boost")]
        public int AtkMaxItemBoost { get; set; } = 0;

        [JsonPropertyName("power_max_item_boost")]
        public int PowerMaxItemBoost { get; set; } = 0;

        // G-Cell Settings - NEW
        [JsonPropertyName("use_gcells")]
        public bool UseGCells { get; set; } = false;

        [JsonPropertyName("gcell_random_encounter_win")]
        public int GCellRandomEncounterWin { get; set; } = 0;

        [JsonPropertyName("gcell_random_encounter_loose")]
        public int GCellRandomEncounterLoose { get; set; } = 0;

        [JsonPropertyName("gcell_battle_win")]
        public int GCellBattleWin { get; set; } = 0;

        [JsonPropertyName("gcell_battle_loose")]
        public int GCellBattleLoose { get; set; } = 0;

        [JsonPropertyName("gcell_training_success")]
        public int GCellTrainingSuccess { get; set; } = 0;

        [JsonPropertyName("gcell_training_phase2_failure")]
        public int GCellTrainingPhase2Failure { get; set; } = 0;

        [JsonPropertyName("gcell_training_phase1_failure")]
        public int GCellTrainingPhase1Failure { get; set; } = 0;

        [JsonPropertyName("gcell_protein")]
        public int GCellProtein { get; set; } = 0;

        [JsonPropertyName("gcell_care_mistake")]
        public int GCellCareMistake { get; set; } = 0;

        [JsonPropertyName("unlocks")]
        public List<Unlock> Unlocks { get; set; }

        [JsonPropertyName("backgrounds")]
        public List<Background> Backgrounds { get; set; }
    }

    public class Unlock
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("version")]
        public int? Version { get; set; }

        [JsonPropertyName("label")]
        public string Label { get; set; }

        [JsonPropertyName("area")]
        public int? Area { get; set; }

        private List<string> _to = new List<string>();
        [JsonPropertyName("to")]
        [JsonConverter(typeof(StringOrStringListConverter))]
        public List<string> To
        {
            get => _to;
            set => _to = value != null ? value.Distinct().ToList() : new List<string>();
        }

        [JsonPropertyName("amount")]
        public int? Amount { get; set; }

        private List<string> _list = new List<string>();
        [JsonPropertyName("list")]
        [JsonConverter(typeof(StringOrStringListConverter))]
        public List<string> List
        {
            get => _list;
            set => _list = value != null ? value.Distinct().ToList() : new List<string>();
        }
    }

    public class Background
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("day_night")]
        public bool DayNight { get; set; }

        [JsonPropertyName("label")]
        public string Label { get; set; }
    }

    public enum RulesetType
    {
        dmc,
        penc,
        dmx,
        vb
    }

    public class StringOrStringListConverter : JsonConverter<List<string>>
    {
        public override List<string> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String)
            {
                var str = reader.GetString();
                return string.IsNullOrWhiteSpace(str)
                    ? new List<string>()
: new List<string>(str.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries));
            }
            else if (reader.TokenType == JsonTokenType.StartArray)
            {
                var list = new List<string>();
                while (reader.Read())
                {
                    if (reader.TokenType == JsonTokenType.EndArray)
                        break;
                    if (reader.TokenType == JsonTokenType.String)
                        list.Add(reader.GetString());
                }
                return list;
            }
            return new List<string>();
        }

        public override void Write(Utf8JsonWriter writer, List<string> value, JsonSerializerOptions options)
        {
            writer.WriteStartArray();
            foreach (var s in value)
                writer.WriteStringValue(s);
            writer.WriteEndArray();
        }
    }
}