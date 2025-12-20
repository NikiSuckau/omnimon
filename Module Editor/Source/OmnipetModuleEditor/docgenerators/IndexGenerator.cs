using OmnipetModuleEditor.Models;
using System.IO;

namespace OmnipetModuleEditor.docgenerators
{
    internal class IndexGenerator
    {
        public static void GenerateIndexPage(string docPath, Module module)
        {
            string template = GeneratorUtils.GetTemplateContent("index.html");
            string content = template.Replace("#MODULENAME", module?.Name ?? "Unknown Module");
            File.WriteAllText(Path.Combine(docPath, "index.html"), content);
        }
    }
}
