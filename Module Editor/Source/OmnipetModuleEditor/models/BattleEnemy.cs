using System.Text.Json.Serialization;

public class BattleEnemy
{
    [JsonPropertyName("name")]
    public string Name { get; set; }

    [JsonPropertyName("power")]
    public int Power { get; set; }

    [JsonPropertyName("attribute")]
    public string Attribute { get; set; }

    [JsonPropertyName("hp")]
    public int Hp { get; set; }

    [JsonPropertyName("area")]
    public int Area { get; set; }

    [JsonPropertyName("round")]
    public int Round { get; set; }

    [JsonPropertyName("version")]
    public int Version { get; set; }

    [JsonPropertyName("handicap")]
    public int Handicap { get; set; }

    [JsonPropertyName("prize")]
    public string Prize { get; set; }

    [JsonPropertyName("unlock")]
    public string Unlock { get; set; }

    [JsonPropertyName("atk_main")]
    public int AtkMain { get; set; }

    [JsonPropertyName("atk_alt")]
    public int AtkAlt { get; set; }

    [JsonPropertyName("stage")]
    public int Stage { get; set; }
}