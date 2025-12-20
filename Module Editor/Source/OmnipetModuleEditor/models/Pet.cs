using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace OmnipetModuleEditor.Models
{
    public class Pet
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("stage")]
        public int Stage { get; set; }

        [JsonPropertyName("version")]
        public int Version { get; set; }

        [JsonPropertyName("special")]
        public bool Special { get; set; }

        [JsonPropertyName("special_key")]
        public string SpecialKey { get; set; }

        [JsonPropertyName("sleeps")]
        public string Sleeps { get; set; }

        [JsonPropertyName("wakes")]
        public string Wakes { get; set; }

        [JsonPropertyName("atk_main")]
        public int AtkMain { get; set; }

        [JsonPropertyName("atk_alt")]
        public int AtkAlt { get; set; }

        [JsonPropertyName("time")]
        public int Time { get; set; }

        [JsonPropertyName("poop_timer")]
        public int PoopTimer { get; set; }

        [JsonPropertyName("energy")]
        public int Energy { get; set; }

        [JsonPropertyName("min_weight")]
        public int MinWeight { get; set; }

        [JsonPropertyName("evol_weight")]
        public int EvolWeight { get; set; }

        [JsonPropertyName("stomach")]
        public int Stomach { get; set; }

        [JsonPropertyName("hunger_loss")]
        public int HungerLoss { get; set; }

        [JsonPropertyName("strength_loss")]
        public int StrengthLoss { get; set; }

        [JsonPropertyName("heal_doses")]
        public int HealDoses { get; set; }

        [JsonPropertyName("power")]
        public int Power { get; set; }

        [JsonPropertyName("attribute")]
        public string Attribute { get; set; }

        [JsonPropertyName("condition_hearts")]
        public int ConditionHearts { get; set; }

        [JsonPropertyName("jogress_avaliable")]
        public bool JogressAvaliable { get; set; }

        [JsonPropertyName("hp")]
        public int Hp { get; set; }

        [JsonPropertyName("star")]
        public int Star { get; set; }

        [JsonPropertyName("attack")]
        public int Attack { get; set; }

        [JsonPropertyName("critical_turn")]
        public int CriticalTurn { get; set; }

        [JsonPropertyName("evolve")]
        public List<Evolution> Evolve { get; set; }
    }

    public enum StageEnum
    {
        EGG = 0,
        FRESH = 1,
        IN_TRAINING = 2,
        ROOKIE = 3,
        CHAMPION = 4,
        ULTIMATE = 5,
        MEGA = 6,
        SUPER_ULTIMATE = 7,
        SUPER_ULTIMATE_PLUS = 8
    }

    public enum AttributeEnum
    {
        FREE = 0,
        DATA = 1,
        VIRUS = 2,
        VACCINE = 3
    }
}