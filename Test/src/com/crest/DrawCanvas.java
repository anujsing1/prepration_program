/**
 * 
 */
package com.crest;

import java.util.ArrayList;


/**
 * @author govind.gupta
 *
 */
public class DrawCanvas {
	
	public static Shape shape;
	public static ArrayList<Shape> shapes;
	public static int cWidth;
	public static int cHeight;

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		shapes = new ArrayList<Shape>(); 
		createCanvas(20, 4);
		System.out.println();
		shape = new Shape('R', 16, 1, 20, 3);
		shapes.add(shape);
		createCanvas();
		System.out.println();
		shape = new Shape('L', 1, 2, 6, 2);
		shapes.add(shape);
		createCanvas();
		System.out.println();
		shape = new Shape('L', 6, 3, 6, 4);
		shapes.add(shape);
		createCanvas();
		System.out.println();
		
//		createCanvasRectangle(20, 5, 2, 2, 15, 5);
	}
	
	public static void createCanvas()
	{
		StringBuilder hLine = createHorizontalLine(cWidth);
		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<cHeight;i++)
		{
			System.out.print("|");
			for(int j=0;j<cWidth-2;j++)
			{
				for (Shape s : shapes)
				{
					if (s.getCmd() == 'L')
					{
						int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2(); 
						if (y1 == y2)
						{
							StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
							drawHLine(i, j, x1, y1, lineToDraw);
						}
						else if (x1==x2)
						{
							drawVLine(i, j, x1, y1, x2, y2);
						}
					}
					else if (s.getCmd() == 'R')
					{
						int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2();
						StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
						
						if (i+1 == y1)
						{
							if (j+1 == x1)
								System.out.print(lineToDraw);
						}
						
						else if (i+1 < y2 && i+1 > y1)
						{
							if(j+1 == x2-2 || j+1 == x1)
							{
								System.out.print('x');
							}
						}
						
						if (i+1 == y2)
						{
							if (j+1 == x1)
								System.out.print(lineToDraw);
						}
					}
				}System.out.print(" ");
			}
			System.out.println("|");
		}
		System.out.print(hLine);
	}
	
	public static void createCanvasLine()
	{
		StringBuilder hLine = createHorizontalLine(cWidth);
		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<cHeight;i++)
		{
			System.out.print("|");
			for(int j=0;j<cWidth-2;j++)
			{
				for (Shape s : shapes)
				{
					int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2(); 
					if (y1 == y2)
					{
						StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
						drawHLine(i, j, x1, y1, lineToDraw);
					}
					else if (x1==x2)
					{
						drawVLine(i, j, x1, y1, x2, y2);
					}
					
				}System.out.print(" ");
			}
			System.out.println("|");
		}
		System.out.print(hLine);
	}
	
	public static void createCanvas(int width, int height)
	{
		cWidth = width;
		cHeight = height;
		StringBuilder hLine = createHorizontalLine(width);

		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<height;i++)
		{
			System.out.print("|");
			for(int j=0;j<width-2;j++)
			{
				System.out.print(" ");
			}
			System.out.println("|");
		}
		System.out.print(hLine);
	}
	
	public static void createCanvasRectangle(int width, int height, int x1, int y1, int x2, int y2)
	{
		StringBuilder hLine = createHorizontalLine(width);
		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<height;i++)
		{
			System.out.print("|");
			for(int j=0;j<width-2;j++)
			{
				StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
				
				if (i+1 == y1)
				{
					if (j+1 == x1)
						System.out.print(lineToDraw);
				}
				
				else if (i+1 < y2 && i+1 > y1)
				{
					if(j+1 == x2-2 || j+1 == x1)
					{
						System.out.print('x');
					}
				}
				
				if (i+1 == y2)
				{
					if (j+1 == x1)
						System.out.print(lineToDraw);
				}
				
				/*}
				else if (x1==x2)
				{
					drawVLine(i, j, x1, y1, x2, y2);
				}*/
				System.out.print(" ");
			}
			System.out.println("|");
		}
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
		if (i+1 >= y1 && i+1 <= y2)
		{
			if (x1 == j+1)
				System.out.print('x');
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
