using OmnimonModuleEditor.Models;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnimonModuleEditor.Utils
{
    /// <summary>
    /// Utility methods for Pet operations and data loading.
    /// </summary>
    public static class PetUtils
    {
        /// <summary>
        /// Fixed name format for all modules - no longer configurable
        /// </summary>
        public const string FixedNameFormat = "$_dmc";

        /// <summary>
        /// Loads pets from the monster.json file.
        /// </summary>
        public static List<Pet> LoadPetsFromJson(string modulePath)
        {
            var pets = new List<Pet>();
            if (string.IsNullOrEmpty(modulePath))
                return pets;

            string monsterPath = Path.Combine(modulePath, "monster.json");
            if (File.Exists(monsterPath))
            {
                try
                {
                    string json = File.ReadAllText(monsterPath);
                    using (var doc = JsonDocument.Parse(json))
                    {
                        var root = doc.RootElement;
                        if (root.TryGetProperty("monster", out var monstersElement))
                        {
                            pets = JsonSerializer.Deserialize<List<Pet>>(monstersElement.GetRawText());
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        string.Format(Properties.Resources.ErrorLoadingMonster, ex.Message),
                        Properties.Resources.Error,
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                }
            }
            return pets;
        }

        public static void SortPets(this List<Pet> pets)
        {
            if (pets == null) return;
            pets.Sort((a, b) =>
            {
                int cmp = a.Version.CompareTo(b.Version);
                if (cmp != 0)
                    if (b.Version == 0) return (cmp * (-1));
                    else return cmp;
                cmp = a.Stage.CompareTo(b.Stage);
                if (cmp != 0) return cmp;
                return string.Compare(a.Name, b.Name, StringComparison.OrdinalIgnoreCase);
            });
        }

        public static Pet ClonePet(Pet pet)
        {
            if (pet == null) return null;
            return new Pet
            {
                Name = pet.Name,
                Stage = pet.Stage,
                Version = pet.Version,
                Special = pet.Special,
                SpecialKey = pet.SpecialKey,
                Sleeps = pet.Sleeps,
                Wakes = pet.Wakes,
                AtkMain = pet.AtkMain,
                AtkAlt = pet.AtkAlt,
                Time = pet.Time,
                PoopTimer = pet.PoopTimer,
                Energy = pet.Energy,
                MinWeight = pet.MinWeight,
                EvolWeight = pet.EvolWeight,
                Stomach = pet.Stomach,
                HungerLoss = pet.HungerLoss,
                StrengthLoss = pet.StrengthLoss,
                HealDoses = pet.HealDoses,
                Power = pet.Power,
                Attribute = pet.Attribute,
                ConditionHearts = pet.ConditionHearts,
                JogressAvaliable = pet.JogressAvaliable,
                Hp = pet.Hp,
                // VB-specific fields - NEW
                Star = pet.Star,
                Attack = pet.Attack,
                CriticalTurn = pet.CriticalTurn,
                Evolve = pet.Evolve != null ? new List<Evolution>(pet.Evolve) : null
            };
        }

        /// <summary>
        /// Loads all pet sprites for a given pet using the new sprite loading system.
        /// </summary>
        public static List<Image> LoadPetSprites(string modulePath, Module module, Pet pet, int spriteCount = 15)
        {
            if (pet == null || string.IsNullOrEmpty(modulePath))
                return new List<Image>();

            bool moduleHighDefinitionSprites = module?.HighDefinitionSprites ?? false;
            var spritesDict = SpriteUtils.LoadPetSprites(pet.Name, modulePath, FixedNameFormat, spriteCount, moduleHighDefinitionSprites);
            return SpriteUtils.ConvertSpritesToList(spritesDict, spriteCount);
        }

        /// <summary>
        /// Loads a single pet sprite (frame 0) for display purposes.
        /// </summary>
        public static Image LoadSinglePetSprite(string petName, string modulePath, Module module = null)
        {
            if (string.IsNullOrEmpty(petName) || string.IsNullOrEmpty(modulePath))
                return null;

            bool moduleHighDefinitionSprites = module?.HighDefinitionSprites ?? false;
            var sprites = SpriteUtils.LoadPetSprites(petName, modulePath, FixedNameFormat, 1, moduleHighDefinitionSprites);
            return sprites.ContainsKey("0") ? sprites["0"] : null;
        }

        public static Dictionary<int, Image> LoadAtkSprites(string modulePath)
        {
            Dictionary<int, Image> atkSprites = new Dictionary<int, Image>();
            // Caminho do fallback: ...\resources\atk
            string modulesDir = Path.GetDirectoryName(modulePath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
            string rootDir = Path.GetDirectoryName(modulesDir); //go to the root directory
            string resourcesAtk = Path.Combine(rootDir, "assets", "atk");

            // Novo: caminho do módulo
            string moduleAtk = Path.Combine(modulePath, "atk");
            bool moduleAtkExists = Directory.Exists(moduleAtk);

            // Dynamically discover all available attack sprites instead of hardcoding to 117
            int i = 1;
            bool foundSprites = true;
            while (foundSprites)
            {
                string path = null;
                if (moduleAtkExists)
                {
                    string customPath = Path.Combine(moduleAtk, $"{i}.png");
                    if (File.Exists(customPath))
                        path = customPath;
                }
                if (path == null)
                {
                    string fallbackPath = Path.Combine(resourcesAtk, $"{i}.png");
                    if (File.Exists(fallbackPath))
                        path = fallbackPath;
                }

                if (path != null)
                {
                    try
                    {
                        atkSprites[i] = Image.FromFile(path);
                    }
                    catch { atkSprites[i] = null; }
                    i++;
                }
                else
                {
                    // No sprite found for this index, stop searching
                    foundSprites = false;
                }
            }
            return atkSprites;
        }

        /// <summary>
        /// Gets the color for a given attribute.
        /// </summary>
        public static Color GetAttributeColor(string attr)
        {
            switch (attr)
            {
                case "Da": return Color.FromArgb(66, 165, 245);      // Data
                case "Va": return Color.FromArgb(102, 187, 106);     // Vaccine
                case "Vi": return Color.FromArgb(237, 83, 80);       // Virus
                case "": return Color.FromArgb(171, 71, 188);        // Free
                default: return Color.FromArgb(171, 71, 188);        // Free (fallback)
            }
        }

        /// <summary>
        /// Converts attribute enum to JSON string.
        /// </summary>
        public static string AttributeEnumToJson(AttributeEnum attr)
        {
            switch (attr)
            {
                case AttributeEnum.DATA: return "Da";
                case AttributeEnum.VACCINE: return "Va";
                case AttributeEnum.VIRUS: return "Vi";
                case AttributeEnum.FREE:
                default: return "";
            }
        }

        /// <summary>
        /// Converts JSON string to attribute enum.
        /// </summary>
        public static AttributeEnum JsonToAttributeEnum(string attr)
        {
            switch (attr)
            {
                case "Da": return AttributeEnum.DATA;
                case "Va": return AttributeEnum.VACCINE;
                case "Vi": return AttributeEnum.VIRUS;
                case "":

                default: return AttributeEnum.FREE;
            }
        }
    }
}