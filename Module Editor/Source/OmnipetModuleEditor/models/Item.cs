using System.Text.Json.Serialization;

namespace OmnipetModuleEditor.Models
{
    public class Item
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; }

        [JsonPropertyName("sprite_name")]
        public string SpriteName { get; set; }

        [JsonPropertyName("effect")]
        public string Effect { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; }

        [JsonPropertyName("amount")]
        public int Amount { get; set; }

        [JsonPropertyName("boost_time")]
        public int BoostTime { get; set; }

        [JsonPropertyName("component_item")]
        public string ComponentItem { get; set; }

        [JsonPropertyName("weight_gain")]
        public int WeightGain { get; set; }
    }

    public enum EffectEnum
    {
        status_change,
        status_boost,
        component,
        digimental
    }

    public enum StatusEnum
    {
        hunger,
        strength,
        hp,
        attack,
        xai_roll,
        skip_to_boss,
        exp_multiplier,
        armor,
        power,
        vital_values,
        timer,
        dp
    }

}