using System;
using System.Text.Json.Serialization;

namespace OmnimonModuleEditor.Models
{
    public enum EventType
    {
        EnemyBattle,
        ItemPackage
    }

    public class Event
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("global")]
        public bool Global { get; set; }

        [JsonPropertyName("type")]
        public EventType Type { get; set; }

        [JsonPropertyName("chance_percent")]
        public double ChancePercent { get; set; }

        [JsonPropertyName("area")]
        public int? Area { get; set; }

        [JsonPropertyName("round")]
        public int? Round { get; set; }

        [JsonPropertyName("item")]
        public string Item { get; set; }

        [JsonPropertyName("item_quantity")]
        public int? ItemQuantity { get; set; }
    }
}
