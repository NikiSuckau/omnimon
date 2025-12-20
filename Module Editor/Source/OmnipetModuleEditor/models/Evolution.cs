using System.Text.Json.Serialization;

namespace OmnipetModuleEditor.Models
{
    public class Evolution
    {
        [JsonPropertyName("to")]
        public string To { get; set; }

        [JsonPropertyName("condition_hearts")]
        public int[] ConditionHearts { get; set; }

        [JsonPropertyName("training")]
        public int[] Training { get; set; }

        [JsonPropertyName("battles")]
        public int[] Battles { get; set; }

        [JsonPropertyName("win_ratio")]
        public int[] WinRatio { get; set; }
        [JsonPropertyName("win_count")]
        public int[] WinCount { get; set; }

        [JsonPropertyName("mistakes")]
        public int[] Mistakes { get; set; }

        [JsonPropertyName("level")]
        public int[] Level { get; set; }

        [JsonPropertyName("overfeed")]
        public int[] Overfeed { get; set; }

        [JsonPropertyName("sleep_disturbances")]
        public int[] SleepDisturbances { get; set; }

        [JsonPropertyName("area")]
        public int? Area { get; set; }

        [JsonPropertyName("stage")]
        public int? Stage { get; set; }

        [JsonPropertyName("version")]
        public int? Version { get; set; }

        [JsonPropertyName("attribute")]
        public string Attribute { get; set; }

        [JsonPropertyName("jogress")]
        public string Jogress { get; set; }
        [JsonPropertyName("jogress_prefix")]
        public bool? JogressPrefix { get; set; }

        [JsonPropertyName("special_encounter")]
        public bool? SpecialEncounter { get; set; }

        [JsonPropertyName("stage-5")]
        public int[] Stage5 { get; set; }
        [JsonPropertyName("stage-6")]
        public int[] Stage6 { get; set; }
        [JsonPropertyName("stage-7")]
        public int[] Stage7 { get; set; }
        [JsonPropertyName("stage-8")]
        public int[] Stage8 { get; set; }

        [JsonPropertyName("item")]
        public string Item { get; set; }
        [JsonPropertyName("time_range")]
        public string[] TimeRange { get; set; }
        [JsonPropertyName("trophies")]
        public int[] Trophies { get; set; }
        [JsonPropertyName("vital_values")]
        public int[] VitalValues { get; set; }
        [JsonPropertyName("weigth")]
        public int[] Weigth { get; set; }
        [JsonPropertyName("quests_completed")]
        public int[] QuestsCompleted { get; set; }
        [JsonPropertyName("pvp")]
        public int[] Pvp { get; set; }

        // New G-Cell evolution criteria
        [JsonPropertyName("gcell_hatch")]
        public bool? GCellHatch { get; set; }

        [JsonPropertyName("blue_gcells")]
        public int[] BlueGCells { get; set; }

        [JsonPropertyName("yellow_gcells")]
        public int[] YellowGCells { get; set; }

        [JsonPropertyName("red_gcells")]
        public int[] RedGCells { get; set; }
    }
}