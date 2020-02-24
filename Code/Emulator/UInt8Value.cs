using System;

namespace Emulator
{
    public class UInt8Value
    {
        public byte Value { get; set; }

        public string HexValue => $"{Value:X2}";

        public string BinValue => Convert.ToString(Value, 2).PadLeft(8, '0');

        public UInt8Value()
        {
        }

        public UInt8Value(byte value)
        {
            Value = value;
        }
    }
}