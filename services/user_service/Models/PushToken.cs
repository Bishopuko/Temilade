using System;

namespace UserService.Models
{
    public class PushToken
    {
        public Guid Id { get; set; }
        public Guid UserId { get; set; }

        public string? Token { get; set; }
        public string? Platform { get; set; } 

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public User? User { get; set; }
    }
}
