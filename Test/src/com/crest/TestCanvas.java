/**
 * 
 */
package com.crest;


/**
 * @author govind.gupta
 *
 */
public class TestCanvas {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
//		createCanvas(20, 5);
		createCanvasLine(20, 5, 2, 2, 6, 2);
		System.out.println();
		createCanvasLine(20, 5, 10, 2, 10, 5);
	}
	
	public static void createCanvas(int width, int height)
	{
		/*for (int i=0;i<width;i++)
		{
			System.out.print("-");
		}*/
		StringBuilder hLine = createHorizontalLine(width);
		StringBuilder vLine = createVerticalLine(height);
		
		System.out.print(hLine);
		System.out.println();
//		System.out.print(hLine);
		
		for(int i=0;i<height;i++)
		{
			System.out.print("|");
			for(int j=0;j<width-2;j++)
			{
				System.out.print(" ");
			}
			System.out.println("|");
		}
		/*for (int i=0;i<width;i++)
		{
			System.out.print("-");
		}*/
		System.out.print(hLine);
	}
	
	public static void createCanvasLine(int width, int height, int x1, int y1, int x2, int y2)
	{
		StringBuilder hLine = createHorizontalLine(width);
		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<height;i++)
		{
			System.out.print("|");
			for(int j=0;j<width-2;j++)
			{
				if (y1 == y2)
				{
					StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
					drawHLine(i, j, x1, y1, lineToDraw);
				}
				else if (x1==x2)
				{
					drawVLine(i, j, x1, y1, x2, y2);
				}
				System.out.print(" ");
			}
			System.out.println("|");
		}
		System.out.print(hLine);
	}
	
	public static void drawVLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		/*if (i+1 == y1)
		{
			if (x1 == j+1)
				System.out.print('|');
		}
		else*/ if (i+1 >= y1 && i+1 <= y2)
		{
			if (x1 == j+1)
				System.out.print('|');
		}
	}
	
	public static void drawHLine(int i, int j, int x1, int y1, StringBuilder lineToDraw)
	{
		if (i+1 == y1)
		{
			if (x1 == j+1)
			{
				System.out.print(lineToDraw);
			}
			/*if (x1 >= j && j <= x2)
			{
				System.out.print('x');
			}*/
		}
	}
	
	public static StringBuilder createHorizontalLine(int width)
	{
		StringBuilder verticalLine = new StringBuilder();
		for (int i=0;i<width;i++)
		{
			verticalLine = verticalLine.append('-');
		}
		return verticalLine;
	}
	
	public static StringBuilder createHorizontalLine(int width, char c)
	{
		StringBuilder verticalLine = new StringBuilder();
		for (int i=0;i<width;i++)
		{
			verticalLine = verticalLine.append(c);
		}
		return verticalLine;
	}
	
	public static StringBuilder createVerticalLine(int height)
	{
		StringBuilder horizontalLine = new StringBuilder();
		for (int i=0;i<height;i++)
		{
			horizontalLine = horizontalLine.append('|');
			horizontalLine = horizontalLine.append('\n');
		}
		return horizontalLine;
	}

}
