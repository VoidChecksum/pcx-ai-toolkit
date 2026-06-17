using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Utilities;
using System.ComponentModel.Composition;

namespace PcxAngelScriptVS
{
#pragma warning disable 649
    // Registers the "angelscript" content type and binds the .as file extension.
    public class AngelScriptContentDefinition
    {
        [Export]
        [Name("angelscript")]
        [BaseDefinition(CodeRemoteContentDefinition.CodeRemoteContentTypeName)]
        internal static ContentTypeDefinition AngelScriptContentTypeDefinition;

        [Export]
        [FileExtension(".as")]
        [ContentType("angelscript")]
        internal static FileExtensionToContentTypeDefinition AngelScriptFileExtensionDefinition;
    }
#pragma warning restore 649
}
