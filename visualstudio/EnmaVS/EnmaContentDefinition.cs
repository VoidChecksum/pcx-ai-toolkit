using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Utilities;
using System.ComponentModel.Composition;

namespace PcxEnmaVS
{
#pragma warning disable 649
    // Registers the "enma" content type and binds the .em file extension to it.
    // Visual Studio loads the language client when an .em file is opened.
    public class EnmaContentDefinition
    {
        [Export]
        [Name("enma")]
        [BaseDefinition(CodeRemoteContentDefinition.CodeRemoteContentTypeName)]
        internal static ContentTypeDefinition EnmaContentTypeDefinition;

        [Export]
        [FileExtension(".em")]
        [ContentType("enma")]
        internal static FileExtensionToContentTypeDefinition EnmaFileExtensionDefinition;
    }
#pragma warning restore 649
}
