namespace Emulator
{
    public class Register
    {
        public Bus BUS { get; set; }

        public byte Value { get; set; }

        public bool Load { get; set; }

        public bool _Out { get; set; }

        public string GetHexValue()
        {
            return null;
        }

        public string GetBinValue()
        {
            return null;
        }
    }
}