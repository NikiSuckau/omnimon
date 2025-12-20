using System.Drawing;

namespace OmnipetModuleEditor.Controls
{
    public class AtkComboItem
    {
        public int Number { get; }
        public Image Sprite { get; }
        public AtkComboItem(int number, Image sprite)
        {
            Number = number;
            Sprite = sprite;
        }
        public override string ToString() => Number == 0 ? "None" : Number.ToString();
    }
}
