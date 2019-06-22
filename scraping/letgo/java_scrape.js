const item = process.argv[2]
const cityname = process.argv.slice(3)[0];
const urlcity = cityname.replace(" ","_").toLowerCase();

const dir = '/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/letgo/'+urlcity+'/'

const puppeteer = require('puppeteer');
const fs = require('fs');

const escapeXpathString = str => {
  const splitedQuotes = str.replace(/'/g, `', "'", '`);
  return `concat('${splitedQuotes}', '')`;
};

const clickByText = async (page, text) => {
  const escapedText = escapeXpathString(text);
  const linkHandlers = await page.$x(`//a[contains(text(), ${escapedText})]`);

  if (linkHandlers.length > 0) {
    await linkHandlers[0].click();
  } else {
    throw new Error(`Link not found: ${text}`);
  }
};
const clickByTextSpan = async (page, text) => {
  const escapedText = escapeXpathString(text);
  const linkHandlers = await page.$x(`//span[contains(text(), ${escapedText})]`);

  if (linkHandlers.length > 0) {
    await linkHandlers[0].click();
  } else {
    throw new Error(`Link not found: ${text}`);
  }
};

async function autoScroll(page){
    await page.evaluate(async () => {
        await new Promise((resolve, reject) => {
            var totalHeight = 0;
            var distance = 200;
            var step=0;
            
            var timer = setInterval(() => {
                step++;
                var scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                //if(totalHeight >= scrollHeight && step < 4){
                if(totalHeight >= scrollHeight){
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

  const context = browser.defaultBrowserContext();
  await context.overridePermissions('https://us.letgo.com/en?searchTerm='+item, ['geolocation']);

  // go to page
  await page.goto('https://us.letgo.com/en?searchTerm='+item);
  await page.setViewport({
      width: 1200,
      height: 800
  });
  await page.waitFor(2000);

  // click "Cancel" on this first pop-up window
  await clickByTextSpan(page, `Cancel`);
  await page.waitFor(2000);

  // Enter in the city name into the Location field and select it
  await clickByTextSpan(page, `Location`);
  await page.type('input[type=search]', cityname, {delay: 20});
  await page.waitFor(4000);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  await page.waitFor(4000);
  // Click on the slider to move the search radius. 
  // So far it's stuck at a 20mi radius
  const e = await page.$('.input-range__track');
  e.click()

  // Click on the "Select Location" button
  await page.waitFor(2000);
  await page.evaluate(() => {
      let elements = document.getElementsByClassName('sc-dnqmqq sc-gZMcBi cCxPJk');
      elements[0].click();
      //let elements = document.getElementsByClassName('.sc-dnqmqq.MapLocationFinderStyle__CompassButton-m7m5vd-3.iesMjT.sc-iwsKbI.fnqZsU');
      //for (let element of elements)
       //   element.click();
      // let element = document.querySelector('MapLocationFinderStyle__ControlsWrapper-m7m5vd-5 dTVZXV');
      // element.click();
  });
  await page.waitFor(1000);

  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(1000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);

  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(2000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(3000);
  await clickByText(page, `Load more`);
  await page.waitFor(6000);
  await clickByText(page, `Load more`);
  //await page.waitFor(6000);
  //await clickByText(page, `Load more`);
  //await page.waitFor(6000);
  //await clickByText(page, `Load more`);

  //await page.evaluate(_ => {
  //window.scrollTo(0, 0);
  //});
  //// scroll down the page to load many more
  //await autoScroll(page);

  const fileLogger = fs.createWriteStream('letgo_'+item+urlcity+'.html')

  const htmlContent = await page.content();
  const util = require('util')
  
  fs.writeFileSync(dir+'letgo_'+item+'.html', htmlContent)

  await browser.close();
})();
