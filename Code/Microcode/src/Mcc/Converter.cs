using System;

namespace Mcc
{
    public static class Converter
    {
        public static byte HexToByte(string hex)
        {
            return Convert.ToByte(hex, 16);            
        }

        public static Int16 HexToInt(string hex)
        {
            return Convert.ToInt16(hex, 16);
        }

        public static UInt16 HexToUInt(string hex)
        {
            return Convert.ToUInt16(hex, 16);
        }

        public static string ByteToHex(byte b)
        {
            return $"{b:X2}";
        }

        public static string IntToHex(Int16 i)
        {
            return $"{i:X4}";
        }

        public static string UIntToHex(UInt16 i)
        {
            return $"{i:X4}";
        }

        public static UInt16 BitsToUInt(string bits)
        {
            return Convert.ToUInt16(bits, 2);
        }
    }
}