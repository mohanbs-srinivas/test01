const axios = require("axios");
const { default: PQueue } = require("p-queue");
const fs = require("fs");

const GITHUB_TOKEN = process.env.GITHUB_TOKEN; // Ensure your token is set in the environment variables
const USERNAME = "CanarysPlayground"; // Replace with the username or organization name
const SIX_MONTHS_AGO = new Date();
SIX_MONTHS_AGO.setMonth(SIX_MONTHS_AGO.getMonth() - 6);

if (!GITHUB_TOKEN) {
  throw new Error(
    "Missing GITHUB_TOKEN. Please set it in the environment variables."
  );
}

async function getAllRepos() {
  let page = 1;
  const repos = [];

  while (true) {
    const response = await axios.get(
      `https://api.github.com/orgs/${USERNAME}/repos`,
      {
        headers: {
          Authorization: `Bearer ${GITHUB_TOKEN}`,
        },
        params: {
          per_page: 100,
          page,
        },
      }
    );

    repos.push(...response.data);

    if (response.data.length < 100) {
      break; // No more pages
    }

    page++;
  }

  return repos;
}

async function getLastCommitDate(repo) {
  try {
    const response = await axios.get(
      `https://api.github.com/repos/${USERNAME}/${repo.name}/commits`,
      {
        headers: {
          Authorization: `Bearer ${GITHUB_TOKEN}`,
        },
        params: {
          per_page: 1,
        },
      }
    );

    const lastCommitDate = new Date(response.data[0].commit.committer.date);
    return lastCommitDate;
  } catch (error) {
    if (error.response && error.response.status === 409) {
      // Empty repository
      return null;
    }
    console.error(`Error fetching commits for ${repo.name}:`, error);
    return null;
  }
}

async function findInactiveRepos() {
  const repos = await getAllRepos();
  const queue = new PQueue({ concurrency: 10 }); // Adjust concurrency as needed
  const inactiveRepos = [];

  await Promise.all(
    repos.map((repo) =>
      queue.add(async () => {
        const lastCommitDate = await getLastCommitDate(repo);
        if (!lastCommitDate || lastCommitDate < SIX_MONTHS_AGO) {
          console.log(`Inactive repository: ${repo.name}`);
          inactiveRepos.push(repo.name);
        }
      })
    )
  );

  fs.writeFileSync("inactive_repos.txt", inactiveRepos.join("\n"), "utf-8");
  console.log(
    "Repositories with no commits in the last 6 months:",
    inactiveRepos
  );
}

findInactiveRepos();
