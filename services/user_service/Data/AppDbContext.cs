using Microsoft.EntityFrameworkCore;
using UserService.Models;

namespace UserService.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<User> ?Users { get; set; }
        public DbSet<UserPreference> ?UserPreferences { get; set; }
        public DbSet<PushToken> ?PushTokens{ get; set; }
    }
}