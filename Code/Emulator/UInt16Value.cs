using System;

namespace Emulator
{
    public class UInt16Value
    {
        public ushort Value 
        { 
            get { return (ushort)((HighByte.Value << 8) + LowByte.Value); }
            set 
            {
                LowByte.Value = (byte)(value & 0xff);
                HighByte.Value = (byte)(value >> 8);
            }
        }

        public UInt8Value LowByte { get; } = new UInt8Value();

        public UInt8Value HighByte { get; } = new UInt8Value();

        public string HexValue => $"{Value:X4}";

        public string BinValue => Convert.ToString(Value, 2).PadLeft(16, '0');

        public UInt16Value()
        {
        }

        public UInt16Value(ushort value)
        {
            Value = value;
        }
    }
}