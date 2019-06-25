const item = process.argv[2]
const cityname = process.argv.slice(3)[0];
const urlcity = cityname.replace(" ","_").toLowerCase();

const puppeteer = require('puppeteer');
const fs = require('fs');

const escapeXpathString = str => {
  const splitedQuotes = str.replace(/'/g, `', "'", '`);
  return `concat('${splitedQuotes}', '')`;
};

const clickByText = async (page, text) => {
  const escapedText = escapeXpathString(text);
  const linkHandlers = await page.$x(`//button[contains(text(), ${escapedText})]`);

  if (linkHandlers.length > 0) {
    await linkHandlers[0].click();
  } else {
    throw new Error(`Link not found: ${text}`);
  }
};

const dir = '/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/offerup/'+urlcity+'/'
const statedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/offerup/states/'

fs.readdir(statedir, function (err, files) {
  if (err) {
    console.error("Could not list the directory.", err);
    process.exit(1);
  };
  files.forEach(function (filestate, index) {
    // Make one pass and make the file complete
    fs.readFile(statedir+filestate, function (err, data) { 
      if (err) throw err;                                
      if(data.includes(cityname)){                  
          urlstate = filestate.substring(0, 2);
          async function autoScroll(page){
              await page.evaluate(async () => {
                  await new Promise((resolve, reject) => {
                      var totalHeight = 0;
                      var distance = 500;
                      var step=0;
                      
                      var timer = setInterval(() => {
                          step++;
                          var scrollHeight = document.body.scrollHeight;
                          window.scrollBy(0, distance);
                          totalHeight += distance;
                          //if(totalHeight >= scrollHeight && step < 4){
                          if(totalHeight > 200000){
                              clearInterval(timer);
                              resolve();
                          }
                      }, 300);
                  });
              });
          }
          
          (async () => {
            const browser = await puppeteer.launch({headless:false});
            const page = await browser.newPage();
          
            // go to races page
            await page.goto('https://offerup.com/explore/sck/'+urlstate+'/'+urlcity+'/'+item+'/');
            await page.setViewport({
                width: 1200,
                height: 800
            });
            // await page.waitFor(1000);
          
            // click on "Load more" button in order to scroll down more
            await clickByText(page, `Load more`);
            await page.waitFor(2000);
          
            // scroll down the page to load many more
            await autoScroll(page);
          
            const allItems = await page.evaluate(
              () => Array.from(document.getElementById("db-item-list").querySelectorAll('a'))
                .map(item => {
                  return {
                    detailUrl: item.getAttribute("href"),
                    imgUrl: item.querySelector("img").getAttribute("src"),
                    info: Array.from(item.querySelectorAll("span")).map(item => item.textContent)
                  }
                })
            )
          
            const fileLogger = fs.createWriteStream(dir+'offerup_'+item+'.json', {
              flags: 'a' // 'a' means appending (old data will be preserved)
            })
            for (const theitem of allItems) {
              fileLogger.write(`${JSON.stringify(theitem)}\n`)
            }
          
            const util = require('util')
            console.log(util.inspect(allItems, { maxArrayLength: null }))
          
            await browser.close();
          })();
      }
    });
  });
});
