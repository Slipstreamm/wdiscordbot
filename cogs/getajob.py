import discord
from discord import app_commands
from discord.ext import commands
import random

CAREER_LINKS = [
    ("National Guard Careers", "https://www.nationalguard.com/careers"),
    ("Google Careers", "https://careers.google.com/"),
    ("Microsoft Careers", "https://careers.microsoft.com/"),
    ("LinkedIn Jobs", "https://www.linkedin.com/jobs/"),
    ("Amazon Jobs", "https://www.amazon.jobs/"),
    ("Apple Careers", "https://www.apple.com/jobs/us/"),
    ("Tesla Careers", "https://www.tesla.com/careers"),
    ("SpaceX Careers", "https://www.spacex.com/careers/"),
    ("IBM Careers", "https://www.ibm.com/employment/"),
    ("Intel Careers", "https://www.intel.com/content/www/us/en/jobs/jobs-at-intel.html"),
    ("Meta Careers", "https://www.metacareers.com/"),
    ("Netflix Jobs", "https://jobs.netflix.com/"),
    ("Disney Careers", "https://jobs.disneycareers.com/"),
    ("Nike Careers", "https://jobs.nike.com/"),
    ("Adidas Careers", "https://careers.adidas-group.com/"),
    ("Walmart Careers", "https://careers.walmart.com/"),
    ("Target Careers", "https://jobs.target.com/"),
    ("Starbucks Careers", "https://www.starbucks.com/careers/"),
    ("McDonald's Careers", "https://careers.mcdonalds.com/"),
    ("Indeed", "https://www.indeed.com/"),
    ("Glassdoor", "https://www.glassdoor.com/"),
    ("CareerBuilder", "https://www.careerbuilder.com/"),
    ("Monster", "https://www.monster.com/"),
    ("ZipRecruiter", "https://www.ziprecruiter.com/"),
    ("SimplyHired", "https://www.simplyhired.com/"),
    ("Upwork", "https://www.upwork.com/"),
    ("Fiverr", "https://www.fiverr.com/"),
    ("Freelancer", "https://www.freelancer.com/"),
    ("Craigslist Jobs", "https://www.craigslist.org/about/sites"),
    ("AngelList", "https://angel.co/jobs"),
    ("We Work Remotely", "https://weworkremotely.com/"),
    ("FlexJobs", "https://www.flexjobs.com/"),
    ("Dice", "https://www.dice.com/"),
    ("GitHub Jobs", "https://jobs.github.com/"),
    ("Stack Overflow Jobs", "https://stackoverflow.com/jobs"),
    ("GovernmentJobs.com", "https://www.governmentjobs.com/"),
    ("USAJobs", "https://www.usajobs.gov/"),
    ("The Muse", "https://www.themuse.com/"),
    ("Hired", "https://hired.com/"),
    ("Snagajob", "https://www.snagajob.com/"),
    ("Workopolis", "https://www.workopolis.com/"),
    ("Jobspresso", "https://jobspresso.co/"),
    ("Remotive", "https://remotive.io/"),
    ("Toptal", "https://www.toptal.com/"),
    ("Behance Jobs", "https://www.behance.net/joblist"),
    ("Dribbble Jobs", "https://dribbble.com/jobs"),
]

class CareerLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        @app_commands.command(name="getajob", description="Get a fucking job.")
        async def careers(self, interaction: discord.Interaction):
            name, url = random.choice(CAREER_LINKS)
            await interaction.response.send_message(f"Get a job. \n**{name}**: {url}")

async def setup(bot):
    await bot.add_cog(CareerLinks(bot))