using System;
using System.Linq;
using System.Text;

namespace Asm
{
    public static class StringUtils
    {
        public static string GetUntilEndOfLine(string input, int start)
        {
            int end = input.IndexOf("\n", start);

            if (end == -1)
            {
                end = input.Length;
            }
            
            return input.Substring(start, end - start);
        }

        public static string Cleanup(string input)
        {
            // Replace Windows-style newlines with Linux-style newlines to avoid parsing issues.
            input = input.Replace("\r\n", "\n");

            // Remove indentations.
            input = input.Replace("\t", " ");
            while (input.Contains("  "))
            {
                input = input.Replace("  ", " ");
            }

            // Remove comments.
            while (input.Contains(";"))
            {
                int commentStart = input.IndexOf(";");
                int commentEnd = input.IndexOf("\n", commentStart);

                if (commentEnd == -1)
                {
                    commentEnd = commentStart + (input.Length - commentStart);
                }

                string beforeComment = input.Substring(0, commentStart);
                string afterComment = input.Substring(commentEnd);

                input = beforeComment + afterComment;
            }

            while (input.Contains(" \n"))
            {
                input = input.Replace(" \n", "\n");
            }

            while (input.Contains("\n "))
            {
                input = input.Replace("\n ", "\n");
            }

            // Remove whitespace lines.
            while (input.Contains("\n\n"))
            {
                input = input.Replace("\n\n", "\n");
            }

            input = input.Replace(" ,", ",");
            input = input.Replace(", ", ",");

            input = input.Trim('\n').Trim();

            return input;
        }

        /// <summary>
        /// Returns data found in between the first two " characters
        /// </summary>
        /// <param name="input"></param>
        /// <param name="start"></param>
        /// <returns></returns>
        public static string ExtractStringData(string input, int start)
        {
            try
            {
                int valueStart = input.IndexOf('"', start);
                int valueEnd = input.IndexOf('"', valueStart + 1);

                return input.Substring(valueStart + 1, valueEnd - valueStart - 1);
            }
            catch (Exception ex)
            {
                throw new AssemblerException($"Could not parse line: {GetUntilEndOfLine(input, start)}\nException: {ex.Message}");
            }
        }

        /// <summary>
        /// Takes a value in any of the supported byte formats and returns it as byte.
        /// </summary>
        /// <param name="input"></param>
        /// <returns></returns>
        public static byte ParseByteValue(string input)
        {
            try
            {
                if (input.StartsWith("'"))
                {
                    // Character
                    return Convert.ToByte(Convert.ToChar(input.Trim('\'')));
                }
                else if (input.StartsWith("$"))
                {
                    // Hexadecimal
                    return Convert.ToByte(input.Substring(1), 16);
                }
                else if (input.StartsWith("%"))
                {
                    // Binary
                    return Convert.ToByte(input.Substring(1), 2);
                }
                else
                {
                    // Assume decimal
                    return Convert.ToByte(input);
                }
            }
            catch (Exception ex)
            {
                throw new AssemblerException($"Error occurred while converting value to byte: {input}\nMessage: {ex.Message}");
            }
        }

        /// <summary>
        /// Takes a value in the support 16-bit word format and returns it as ushort.
        /// </summary>
        /// <param name="input"></param>
        /// <returns></returns>
        public static ushort ParseUshortValue(string input)
        {
            if (string.IsNullOrEmpty(input) || input.Length < 2 || !input.StartsWith("$"))
            {
                throw new AssemblerException($"Invalid 16-bit value defined: {input}\n16-bit values must be expressed in hexadecimal format.");
            }

            try
            {
                string hex = input.Substring(1);
                return Convert.ToUInt16(hex, 16);
            }
            catch (Exception ex)
            {
                throw new AssemblerException($"Failed to convert value {input} to 16-bit unsigned integer.\nMessage: {ex.Message}");
            }
        }

        /// <summary>
        /// Takes a data definition in any support format and converts it to bytes.
        /// </summary>
        /// <param name="input"></param>
        /// <returns></returns>
        public static byte[] ParseDataValue(string input)
        {
            if (input.StartsWith('"'))
            {
                // Data is defined as string
                bool terminateString = true;
  
                if (input.EndsWith("_"))
                {
                    terminateString = false;
                    input = input.Substring(0, input.Length - 1).Trim();
                }

                input = ExtractStringData(input, 0);
                input = ReplaceEscapeCharacters(input);

                var bytes = Encoding.ASCII.GetBytes(input).ToList();
                
                if (terminateString)
                {
                    bytes.Add(0);
                }

                return bytes.ToArray();
            }

            // Data is defined as comma separate bytes.
            return input.Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Select(x => ParseByteValue(x))
                .ToArray();
        }

        private static string ReplaceEscapeCharacters(string input)
        {
            string replace = input;

            try
            {
                while (replace.IndexOf(@"\") > -1)
                {
                    int start = replace.IndexOf(@"\");
                    
                    if (replace.Substring(start + 1, 1) == @"\")
                    {
                        // This escape is used to express a backslash.
                        replace = replace.Substring(0, start) + "&backslash;" + replace.Substring(start + 2);
                    }
                    else
                    {
                        string hex = replace.Substring(start + 1, 2);
                        replace = replace.Substring(0, start) + Convert.ToChar(Convert.ToByte(hex, 16)) + replace.Substring(start + 3);
                    }
                }

                return replace.Replace("&backslash;", @"\");
            }
            catch (Exception ex)
            {
                throw new AssemblerException($"Error occurred while replace escape characters in string: {input}\nMessage: {ex.Message}");
            }
        }
    }
}