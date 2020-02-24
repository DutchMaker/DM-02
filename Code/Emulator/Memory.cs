namespace Emulator
{
    public class Memory
    {
        public BusConnections BUS { get; set; }

        public Clock CLOCK { get; set; }

        public UInt8Value Value { get; set; }

        public bool Out { get; set; }

        public bool Load { get; set; }

        public void Tick()
        {
        }
    }
}