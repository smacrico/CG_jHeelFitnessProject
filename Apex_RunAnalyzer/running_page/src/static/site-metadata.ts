interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  logo: string;
  navLinks: {
    name: string;
    url: string;
  }[];
}

const data: ISiteMetadataResult = {
  siteTitle: 'Running for a purpose',
  siteUrl: 'https://www.msfighter.com/',
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU',
  description: 'MSfighter : Personal site and blog',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://www.msfighter.com/blog',
    },
    {
      name: 'smacrico',
      url: 'https://www.msfighter.com/',
    },
  ],
};

export default data;
