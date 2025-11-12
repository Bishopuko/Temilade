namespace UserService.Models
{
    public class UserPreference
    {
        public Guid Id { get; set; }
        public Guid UserId { get; set; }

        public bool EmailEnabled { get; set; }

        public bool PushEnabled { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime LastUpdatedAt { get; set; } = DateTime.UtcNow;

        public User? User { get; set; } 
    }
}